# -*- coding: utf-8 -*-
"""
JugiAI – yksinkertainen Tkinter-pohjainen chat-sovellus OpenAI:lle.

Ominaisuudet:
- Keskustelu jatkuu niin kauan kuin jatkat (säilyttää session muistissa ajon ajan).
- Asetukset (⚙️): API-avain, malli, system-prompt, temperature, top_p, max_tokens, presence/frequency penalty.
- Ensimmäisellä käynnistyksellä pyytää API-avaimen ja asetukset.

Riippuvuudet: Vain Python 3:n standardikirjastot (tkinter, json, urllib). Ei vaadi asennuksia.
"""
from __future__ import annotations

import json
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
from typing import Any, Dict, List

import urllib.request
import urllib.error


CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")


DEFAULT_CONFIG: Dict[str, Any] = {
    "api_key": "",
    "model": "gpt-4o-mini",
    "system_prompt": (
        "You are JugiAI, a helpful, concise assistant. "
        "Respond in the user's language by default."
    ),
    "temperature": 0.7,
    "top_p": 1.0,
    "max_tokens": None,  # None tai numero
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0,
    # Backend: "openai" tai "local"
    "backend": "openai",
    # Paikallinen malli
    "local_model_path": "",
    "local_threads": 0,  # 0 = auto
    # Taustakuva / ikoni
    "show_background": True,
    "background_path": "",
    "background_subsample": 2,
    "background_opacity": 0.18,
    # Typografia/kontrasti
    "font_size": 12,
}


class JugiAIApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("JugiAI")
        self.minsize(720, 480)

        self.config_dict = self.load_config()
        self.history: List[Dict[str, str]] = []  # {role:"user"|"assistant", content:str}
        self._wm_img = None
        self._wm_raw_img = None
        self._wm_scaled_img = None
        self._wm_overlay: tk.Label | None = None
        self.llm = None
        self.llm_model_path = None

        self._build_ui()

        # Jos avain puuttuu, avaa asetukset heti
        if not self.config_dict.get("api_key"):
            self.after(200, self.open_settings)

        # Lataa historia ja ikonit/tausta
        self.load_history()
        self._apply_icon_from_config()
        self._load_watermark_image()
        self._insert_watermark_if_needed()

    # --- UI ---
    def _build_ui(self) -> None:
        root = self

        # Header
        header = ttk.Frame(root)
        header.pack(side=tk.TOP, fill=tk.X)

        title_lbl = ttk.Label(header, text="JugiAI", font=("Segoe UI", 12, "bold"))
        title_lbl.pack(side=tk.LEFT, padx=(10, 6), pady=6)

        self.status_var = tk.StringVar(value="Valmis")
        status_lbl = ttk.Label(header, textvariable=self.status_var, foreground="#6b7280")
        status_lbl.pack(side=tk.LEFT, padx=6)

        # Backend quick toggle
        ttk.Label(header, text="Tausta:").pack(side=tk.RIGHT, padx=(0, 4))
        self.backend_var_quick = tk.StringVar(value=self.config_dict.get("backend", "openai"))
        backend_combo = ttk.Combobox(header, textvariable=self.backend_var_quick, values=["openai", "local"], width=8, state="readonly")
        backend_combo.pack(side=tk.RIGHT, padx=(0, 8), pady=6)
        def on_backend_change(event=None):
            self.config_dict["backend"] = self.backend_var_quick.get()
            self.save_config()
        backend_combo.bind("<<ComboboxSelected>>", on_backend_change)

        settings_btn = ttk.Button(header, text="⚙️", width=3, command=self.open_settings)
        settings_btn.pack(side=tk.RIGHT, padx=(6, 10), pady=6)
        clear_btn = ttk.Button(header, text="Tyhjennä", command=self.clear_history)
        clear_btn.pack(side=tk.RIGHT, pady=6)

        # Chat area
        chat_container = ttk.Frame(root)
        chat_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(4, 6))

        self.chat = tk.Text(
            chat_container,
            wrap=tk.WORD,
            state=tk.DISABLED,
            yscrollcommand=self._on_chat_scroll,
        )
        self.chat.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._chat_scrollbar = ttk.Scrollbar(
            chat_container, orient=tk.VERTICAL, command=self.chat.yview
        )
        self._chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Dark-ish theme for contrast
        try:
            fs = int(self.config_dict.get("font_size", 12))
        except Exception:
            fs = 12
        self.chat.configure(bg="#0b1220", fg="#e5e7eb", insertbackground="#e5e7eb", font=("Segoe UI", fs))
        self.chat.bind("<Configure>", lambda event: self._position_watermark_overlay())

        # Tagit rooleille
        self.chat.tag_configure("role_user", foreground="#93c5fd")
        self.chat.tag_configure("role_assistant", foreground="#34d399")
        self.chat.tag_configure("error", foreground="#f87171")

        # Input area
        input_frame = ttk.Frame(root)
        input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=8)

        self.input = tk.Text(input_frame, height=3, wrap=tk.WORD)
        self.input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input.configure(bg="#111827", fg="#e5e7eb", insertbackground="#e5e7eb", font=("Segoe UI", fs))

        self.send_btn = ttk.Button(input_frame, text="Lähetä", command=self.on_send)
        self.send_btn.pack(side=tk.LEFT, padx=(8, 0))

        # Enter = lähetys, Shift+Enter = rivinvaihto
        self.input.bind("<Shift-Return>", self._newline)
        self.input.bind("<Return>", self._enter_send)

    def _newline(self, event):
        self.input.insert(tk.INSERT, "\n")
        return "break"

    def _enter_send(self, event):
        self.on_send()
        return "break"

    def _on_chat_scroll(self, first: str, last: str) -> None:
        self._chat_scrollbar.set(first, last)
        self._position_watermark_overlay()

    # --- Config persistence ---
    def load_config(self) -> Dict[str, Any]:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # yhdistä puuttuvat oletukset
                merged = {**DEFAULT_CONFIG, **data}
                return merged
            except Exception:
                pass
        return DEFAULT_CONFIG.copy()

    def save_config(self) -> None:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config_dict, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Virhe", f"Asetusten tallennus epäonnistui: {e}")

    # --- Chat helpers ---
    def append_message(self, role: str, content: str) -> None:
        self.chat.configure(state=tk.NORMAL)
        tag = "role_assistant" if role == "assistant" else "role_user"
        header = "JugiAI" if role == "assistant" else "Käyttäjä"
        self.chat.insert(tk.END, f"{header}:\n", tag)
        self.chat.insert(tk.END, content.strip() + "\n\n")
        self.chat.see(tk.END)
        self.chat.configure(state=tk.DISABLED)

    def append_error(self, content: str) -> None:
        self.chat.configure(state=tk.NORMAL)
        self.chat.insert(tk.END, "Virhe:\n", ("error",))
        self.chat.insert(tk.END, content.strip() + "\n\n")
        self.chat.see(tk.END)
        self.chat.configure(state=tk.DISABLED)

    # --- Events ---
    def on_send(self) -> None:
        text = self.input.get("1.0", tk.END).strip()
        if not text:
            return
        if self.config_dict.get("backend", "openai").lower() == "openai":
            if not self.config_dict.get("api_key"):
                messagebox.showinfo("Asetukset tarvitaan", "Syötä OpenAI API -avain asetuksiin.")
                self.open_settings()
                return

        # UI-tila ja viestit
        self.input.delete("1.0", tk.END)
        self.append_message("user", text)
        self.history.append({"role": "user", "content": text})
        self.save_history()

        self.set_busy(True)
        threading.Thread(target=self._worker_call_openai, daemon=True).start()

    def set_busy(self, busy: bool) -> None:
        if busy:
            self.status_var.set("Kirjoittaa…")
            self.send_btn.configure(state=tk.DISABLED)
        else:
            self.status_var.set("Valmis")
            self.send_btn.configure(state=tk.NORMAL)

    # --- Model call ---
    def _worker_call_openai(self) -> None:
        try:
            assistant_text = self.call_model_backend()
        except Exception as e:
            msg = str(e)
            self.after(0, lambda: self.append_error(msg))
            self.after(0, lambda: self.set_busy(False))
            return

        self.history.append({"role": "assistant", "content": assistant_text})
        self.after(0, lambda: self.append_message("assistant", assistant_text))
        self.after(0, self.save_history)
        self.after(0, lambda: self.set_busy(False))

    def call_model_backend(self) -> str:
        backend = self.config_dict.get("backend", "openai").lower()
        if backend == "local":
            return self._call_local_llm()
        return self._call_openai()

    def _call_openai(self) -> str:
        cfg = self.config_dict
        api_key = cfg.get("api_key")
        if not api_key:
            raise RuntimeError("API-avain puuttuu asetuksista.")

        url = "https://api.openai.com/v1/chat/completions"

        messages: List[Dict[str, str]] = []
        sys_prompt = (cfg.get("system_prompt") or "").strip()
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})
        messages.extend(self.history)

        payload: Dict[str, Any] = {
            "model": cfg.get("model", "gpt-4o-mini"),
            "messages": messages,
            "temperature": float(cfg.get("temperature", 0.7)),
            "top_p": float(cfg.get("top_p", 1.0)),
            "presence_penalty": float(cfg.get("presence_penalty", 0.0)),
            "frequency_penalty": float(cfg.get("frequency_penalty", 0.0)),
        }
        max_tokens = cfg.get("max_tokens")
        if isinstance(max_tokens, int) and max_tokens > 0:
            payload["max_tokens"] = max_tokens

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                body = resp.read()
        except urllib.error.HTTPError as e:
            try:
                err_body = e.read().decode("utf-8", errors="ignore")
            except Exception:
                err_body = str(e)
            raise RuntimeError(f"API virhe: {e.code} {err_body}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Verkkovirhe: {e}")

        try:
            j = json.loads(body.decode("utf-8"))
        except Exception:
            raise RuntimeError("Palvelun vastausta ei voitu jäsentää JSONiksi.")

        try:
            content = j["choices"][0]["message"]["content"]
        except Exception:
            content = json.dumps(j, ensure_ascii=False)
        return content or ""

    def _call_local_llm(self) -> str:
        cfg = self.config_dict
        model_path = (cfg.get("local_model_path") or "").strip()
        if not model_path or not os.path.exists(model_path):
            raise RuntimeError("Paikallista mallia ei ole valittu (.gguf). Avaa asetukset.")
        try:
            from llama_cpp import Llama
        except Exception:
            raise RuntimeError("Asenna paikallista mallia varten: pip install llama-cpp-python")

        if self.llm is None or self.llm_model_path != model_path:
            self.llm = Llama(
                model_path=model_path,
                n_threads=int(cfg.get("local_threads", 0)) or None,
                verbose=False,
            )
            self.llm_model_path = model_path

        messages: List[Dict[str, str]] = []
        sys_prompt = (cfg.get("system_prompt") or "").strip()
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})
        messages.extend(self.history)

        params = {
            "messages": messages,
            "temperature": float(cfg.get("temperature", 0.7)),
            "top_p": float(cfg.get("top_p", 1.0)),
        }
        mt = cfg.get("max_tokens")
        if isinstance(mt, int) and mt > 0:
            params["max_tokens"] = mt
        try:
            out = self.llm.create_chat_completion(**params)
            content = out["choices"][0]["message"]["content"]
        except Exception:
            # Fallback yksinkertaiseen prompttiin
            user_texts = "\n\n".join([m["content"] for m in self.history if m["role"] == "user"]) or ""
            prompt = (sys_prompt + "\n\n" + user_texts).strip()
            out = self.llm(
                prompt=prompt,
                temperature=float(cfg.get("temperature", 0.7)),
                top_p=float(cfg.get("top_p", 1.0)),
                max_tokens=mt if isinstance(mt, int) and mt > 0 else 256,
            )
            content = out.get("choices", [{}])[0].get("text", "")
        return content or ""

    # --- Persistence ---
    def load_history(self) -> None:
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
                for m in self.history:
                    self.append_message(m.get("role", "user"), m.get("content", ""))
            except Exception:
                self.history = []

    def save_history(self) -> None:
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def clear_history(self) -> None:
        if not messagebox.askyesno("Vahvista", "Tyhjennetäänkö keskustelu?"):
            return
        self.history = []
        self.chat.configure(state=tk.NORMAL)
        self.chat.delete("1.0", tk.END)
        self.chat.configure(state=tk.DISABLED)
        self.save_history()
        self._insert_watermark_if_needed()

    # --- Settings dialog ---
    def open_settings(self) -> None:
        dlg = tk.Toplevel(self)
        dlg.title("Asetukset – JugiAI")
        dlg.transient(self)
        dlg.grab_set()
        dlg.geometry("720x740")

        original_show_background = bool(self.config_dict.get("show_background", True))
        original_opacity = float(
            self.config_dict.get("background_opacity", DEFAULT_CONFIG["background_opacity"])
        )

        outer = ttk.Frame(dlg, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)

        notebook = ttk.Notebook(outer)
        notebook.pack(fill=tk.BOTH, expand=True)

        tab_general = ttk.Frame(notebook)
        tab_openai = ttk.Frame(notebook)
        tab_local = ttk.Frame(notebook)
        tab_ui = ttk.Frame(notebook)
        notebook.add(tab_general, text="Yleiset")
        notebook.add(tab_openai, text="OpenAI")
        notebook.add(tab_local, text="Paikallinen")
        notebook.add(tab_ui, text="Ulkoasu")
        # --- Tabs content ---
        # General
        g = tab_general
        row = 0
        ttk.Label(g, text="Taustajärjestelmä:").grid(row=row, column=0, sticky=tk.W)
        backend_var = tk.StringVar(value=self.config_dict.get("backend", "openai"))
        backend_box = ttk.Combobox(g, textvariable=backend_var, values=["openai", "local"], state="readonly")
        backend_box.grid(row=row, column=1, sticky=tk.EW, padx=(8, 0))
        row += 1
        ttk.Label(g, text="System-prompt:").grid(row=row, column=0, sticky=tk.NW, pady=(8, 0))
        prompt_txt = ScrolledText(g, height=6, wrap=tk.WORD)
        prompt_txt.insert("1.0", self.config_dict.get("system_prompt", DEFAULT_CONFIG["system_prompt"]))
        prompt_txt.grid(row=row, column=1, sticky=tk.EW, padx=(8, 0), pady=(8, 0))
        row += 1
        ttk.Label(g, text="Temperature (0–2):").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        temp_var = tk.DoubleVar(value=float(self.config_dict.get("temperature", 0.7)))
        ttk.Scale(g, from_=0.0, to=2.0, variable=temp_var).grid(row=row, column=1, sticky=tk.EW, padx=(8, 0), pady=(8, 0))
        row += 1
        ttk.Label(g, text="top_p (0–1):").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        top_p_var = tk.DoubleVar(value=float(self.config_dict.get("top_p", 1.0)))
        ttk.Scale(g, from_=0.0, to=1.0, variable=top_p_var).grid(row=row, column=1, sticky=tk.EW, padx=(8, 0), pady=(8, 0))
        row += 1
        ttk.Label(g, text="max_tokens (tyhjä = ei rajaa):").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        mt_var = tk.StringVar(value=str(self.config_dict.get("max_tokens")) if self.config_dict.get("max_tokens") else "")
        ttk.Entry(g, textvariable=mt_var).grid(row=row, column=1, sticky=tk.EW, padx=(8, 0), pady=(8, 0))
        row += 1
        ttk.Label(g, text="presence_penalty (-2–2):").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        pp_var = tk.DoubleVar(value=float(self.config_dict.get("presence_penalty", 0.0)))
        ttk.Scale(g, from_=-2.0, to=2.0, variable=pp_var).grid(row=row, column=1, sticky=tk.EW, padx=(8, 0), pady=(8, 0))
        row += 1
        ttk.Label(g, text="frequency_penalty (-2–2):").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        fp_var = tk.DoubleVar(value=float(self.config_dict.get("frequency_penalty", 0.0)))
        ttk.Scale(g, from_=-2.0, to=2.0, variable=fp_var).grid(row=row, column=1, sticky=tk.EW, padx=(8, 0), pady=(8, 0))
        row += 1
        for i in range(2):
            g.columnconfigure(i, weight=1)

        # OpenAI tab
        o = tab_openai
        row = 0
        ttk.Label(o, text="OpenAI API Key:").grid(row=row, column=0, sticky=tk.W)
        api_var = tk.StringVar(value=self.config_dict.get("api_key", ""))
        ttk.Entry(o, textvariable=api_var, show="*").grid(row=row, column=1, sticky=tk.EW, padx=(8, 0))
        row += 1
        ttk.Label(o, text="Malli (OpenAI):").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        model_var = tk.StringVar(value=self.config_dict.get("model", "gpt-4o-mini"))
        ttk.Entry(o, textvariable=model_var).grid(row=row, column=1, sticky=tk.EW, padx=(8, 0), pady=(8, 0))
        row += 1
        for i in range(2):
            o.columnconfigure(i, weight=1)

        # Local tab
        l = tab_local
        row = 0
        ttk.Label(l, text="Paikallinen malli (.gguf):").grid(row=row, column=0, sticky=tk.W)
        lpath_var = tk.StringVar(value=self.config_dict.get("local_model_path", ""))
        ttk.Entry(l, textvariable=lpath_var).grid(row=row, column=1, sticky=tk.EW, padx=(8, 0))
        def choose_gguf():
            p = filedialog.askopenfilename(filetypes=[("GGUF models", "*.gguf"), ("All files", "*.*")])
            if p:
                lpath_var.set(p)
        ttk.Button(l, text="Valitse…", command=choose_gguf).grid(row=row, column=2, sticky=tk.W, padx=(8, 0))
        row += 1
        ttk.Label(l, text="Säikeet (0 = auto):").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        lthr_var = tk.IntVar(value=int(self.config_dict.get("local_threads", 0)))
        ttk.Entry(l, textvariable=lthr_var).grid(row=row, column=1, sticky=tk.W, padx=(8, 0), pady=(8, 0))
        row += 1
        for i in range(3):
            l.columnconfigure(i, weight=1)

        # UI tab
        u = tab_ui
        row = 0
        ttk.Label(u, text="Taustakuva (PNG):").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        bg_var = tk.StringVar(value=self.config_dict.get("background_path", ""))
        ttk.Entry(u, textvariable=bg_var).grid(row=row, column=1, sticky=tk.EW, padx=(8, 0), pady=(8, 0))
        def choose_bg():
            p = filedialog.askopenfilename(filetypes=[("Kuvat", "*.png;*.gif"), ("Kaikki", "*.*")])
            if p:
                bg_var.set(p)
        ttk.Button(u, text="Valitse…", command=choose_bg).grid(row=row, column=2, sticky=tk.W, padx=(8, 0), pady=(8, 0))
        row += 1
        opacity_var = tk.DoubleVar(
            value=float(
                self.config_dict.get(
                    "background_opacity", DEFAULT_CONFIG["background_opacity"]
                )
            )
        )
        show_bg_var = tk.BooleanVar(value=original_show_background)
        ttk.Checkbutton(u, text="Näytä taustakuva/watermark", variable=show_bg_var).grid(row=row, column=1, sticky=tk.W)
        
        def _on_show_bg_toggle(*_args: Any) -> None:
            enabled = bool(show_bg_var.get())
            if enabled:
                self._load_watermark_image(respect_visibility=False)
                self._preview_watermark_opacity(opacity_var.get(), respect_visibility=False)
            else:
                self._remove_watermark_overlay()

        show_bg_var.trace_add("write", _on_show_bg_toggle)
        row += 1
        ttk.Label(u, text="Taustakuvan läpinäkyvyys (0–1):").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        opacity_scale = ttk.Scale(u, from_=0.0, to=1.0, variable=opacity_var)
        opacity_scale.grid(row=row, column=1, sticky=tk.EW, padx=(8, 0), pady=(8, 0))
        opacity_value_lbl = ttk.Label(u, text=f"{opacity_var.get():.2f}")
        opacity_value_lbl.grid(row=row, column=2, sticky=tk.W, padx=(8, 0))

        def _on_opacity_change(*_args: Any) -> None:
            try:
                value = float(opacity_var.get())
            except Exception:
                value = original_opacity
            value = max(0.0, min(1.0, value))
            opacity_value_lbl.configure(text=f"{value:.2f}")
            if show_bg_var.get():
                self._preview_watermark_opacity(value, respect_visibility=False)
            else:
                self._remove_watermark_overlay()

        opacity_var.trace_add("write", _on_opacity_change)
        _on_opacity_change()
        row += 1
        ttk.Label(u, text="Watermark-koko (1–8, suurempi = pienempi kuva):").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        subs_var = tk.IntVar(value=int(self.config_dict.get("background_subsample", 2)))
        ttk.Spinbox(u, from_=1, to=8, textvariable=subs_var, width=5).grid(row=row, column=1, sticky=tk.W, padx=(8, 0), pady=(8, 0))
        row += 1
        ttk.Label(u, text="Fonttikoko (pt):").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        fsize_var = tk.IntVar(value=int(self.config_dict.get("font_size", 12)))
        ttk.Spinbox(u, from_=9, to=20, textvariable=fsize_var, width=5).grid(row=row, column=1, sticky=tk.W, padx=(8, 0), pady=(8, 0))
        row += 1
        for i in range(3):
            u.columnconfigure(i, weight=1)

        # Buttons
        # Footer buttons (use pack to avoid mixing with grid in same container)
        btns = ttk.Frame(outer)
        btns.pack(side=tk.BOTTOM, fill=tk.X, pady=(12, 0))

        def cancel_and_close() -> None:
            self._load_watermark_image()
            if original_show_background:
                self._preview_watermark_opacity(original_opacity)
            else:
                self._remove_watermark_overlay()
            dlg.destroy()

        ttk.Button(btns, text="Sulje tallentamatta", command=cancel_and_close).pack(side=tk.RIGHT)

        def save_and_close():
            # tallenna arvot
            self.config_dict["api_key"] = api_var.get().strip()
            self.config_dict["model"] = model_var.get().strip() or DEFAULT_CONFIG["model"]
            self.config_dict["system_prompt"] = prompt_txt.get("1.0", tk.END).strip() or DEFAULT_CONFIG["system_prompt"]
            self.config_dict["temperature"] = float(f"{temp_var.get():.3f}")
            self.config_dict["top_p"] = float(f"{top_p_var.get():.3f}")
            mt = mt_var.get().strip()
            self.config_dict["max_tokens"] = int(mt) if mt.isdigit() else None
            self.config_dict["presence_penalty"] = float(f"{pp_var.get():.3f}")
            self.config_dict["frequency_penalty"] = float(f"{fp_var.get():.3f}")
            self.config_dict["backend"] = backend_var.get().strip() or "openai"
            # Sync quick toggle too
            self.backend_var_quick.set(self.config_dict["backend"]) 
            self.config_dict["local_model_path"] = lpath_var.get().strip()
            self.config_dict["local_threads"] = int(lthr_var.get()) if str(lthr_var.get()).isdigit() else 0
            self.config_dict["background_path"] = bg_var.get().strip()
            self.config_dict["show_background"] = bool(show_bg_var.get())
            try:
                self.config_dict["background_subsample"] = max(1, min(8, int(subs_var.get())))
            except Exception:
                self.config_dict["background_subsample"] = 2
            try:
                opacity_val = float(opacity_var.get())
            except Exception:
                opacity_val = DEFAULT_CONFIG["background_opacity"]
            opacity_val = max(0.0, min(1.0, opacity_val))
            self.config_dict["background_opacity"] = float(f"{opacity_val:.3f}")
            try:
                self.config_dict["font_size"] = max(9, min(20, int(fsize_var.get())))
            except Exception:
                self.config_dict["font_size"] = 12
            self.save_config()
            self._apply_icon_from_config()
            self._load_watermark_image()
            self._insert_watermark_if_needed()
            # Apply font size live
            fs = int(self.config_dict.get("font_size", 12))
            self.chat.configure(font=("Segoe UI", fs))
            self.input.configure(font=("Segoe UI", fs))
            dlg.destroy()

        ttk.Button(btns, text="Tallenna", command=save_and_close).pack(side=tk.RIGHT, padx=(0, 8))

        dlg.protocol("WM_DELETE_WINDOW", cancel_and_close)

        for i in range(2):
            outer.columnconfigure(i, weight=1)

    # --- Icon & background helpers ---
    def _resolve_default_logo(self) -> str:
        candidate = (self.config_dict.get("background_path") or "").strip()
        if candidate and os.path.exists(candidate):
            return candidate
        here = os.path.dirname(__file__)
        for p in [os.path.join(here, "logo.png"), os.path.join(here, "..", "logo.png")]:
            if os.path.exists(p):
                return p
        return ""

    def _apply_icon_from_config(self) -> None:
        path = self._resolve_default_logo()
        if not path:
            return
        try:
            img = tk.PhotoImage(file=path)
            self.iconphoto(True, img)
            self._app_icon_ref = img
        except Exception:
            pass

    def _load_watermark_image(self, respect_visibility: bool = True) -> None:
        self._wm_img = None
        self._wm_raw_img = None
        self._wm_scaled_img = None
        if respect_visibility and not self.config_dict.get("show_background", True):
            self._remove_watermark_overlay()
            return
        path = self._resolve_default_logo()
        if not path:
            self._remove_watermark_overlay()
            return
        try:
            raw_img = tk.PhotoImage(file=path)
        except Exception:
            self._remove_watermark_overlay()
            return
        subs = int(self.config_dict.get("background_subsample", 2))
        subs = max(1, min(8, subs))
        try:
            scaled = raw_img.subsample(subs, subs) if subs > 1 else raw_img.copy()
        except Exception:
            scaled = raw_img
        opacity_val = float(self.config_dict.get("background_opacity", DEFAULT_CONFIG["background_opacity"]))
        opacity_val = max(0.0, min(1.0, opacity_val))
        processed = self._apply_watermark_opacity(scaled, opacity_val)
        self._wm_raw_img = raw_img
        self._wm_scaled_img = scaled
        self._wm_img = processed

    def _insert_watermark_if_needed(self) -> None:
        if not self._wm_img:
            self._remove_watermark_overlay()
            return
        self._ensure_watermark_overlay()
        self._position_watermark_overlay()

    def _ensure_watermark_overlay(self) -> None:
        if not self._wm_img:
            self._remove_watermark_overlay()
            return
        bg_color = "#0b1220"
        try:
            bg_color = self.chat.cget("bg")
        except Exception:
            pass
        if self._wm_overlay is None:
            self._wm_overlay = tk.Label(
                self.chat,
                image=self._wm_img,
                borderwidth=0,
                highlightthickness=0,
                background=bg_color,
                cursor="arrow",
            )
            self._wm_overlay.image = self._wm_img
            self._bind_overlay_events()
        else:
            self._wm_overlay.configure(image=self._wm_img, background=bg_color)
            self._wm_overlay.image = self._wm_img

    def _bind_overlay_events(self) -> None:
        if not self._wm_overlay:
            return

        def forward(sequence: str):
            def _handler(event: tk.Event) -> str:
                if not self._wm_overlay:
                    return "break"
                x = event.x + self._wm_overlay.winfo_x()
                y = event.y + self._wm_overlay.winfo_y()
                self.chat.event_generate(sequence, x=x, y=y, state=event.state)
                return "break"

            return _handler

        for seq in ("<ButtonPress-1>", "<B1-Motion>", "<ButtonRelease-1>"):
            self._wm_overlay.bind(seq, forward(seq))
        self._wm_overlay.bind("<MouseWheel>", self._forward_mousewheel)
        self._wm_overlay.bind("<Button-4>", self._forward_mousewheel)
        self._wm_overlay.bind("<Button-5>", self._forward_mousewheel)

    def _forward_mousewheel(self, event: tk.Event) -> str:
        if event.num == 4:
            self.chat.yview_scroll(-1, "units")
        elif event.num == 5:
            self.chat.yview_scroll(1, "units")
        else:
            delta = event.delta or 0
            if delta:
                self.chat.yview_scroll(int(-delta / 120), "units")
        return "break"

    def _position_watermark_overlay(self) -> None:
        if not self._wm_overlay or not self._wm_img:
            return
        try:
            self._wm_overlay.place(relx=0.5, rely=0.5, anchor="center")
        except Exception:
            pass

    def _remove_watermark_overlay(self) -> None:
        if self._wm_overlay is not None:
            try:
                self._wm_overlay.destroy()
            except Exception:
                pass
            self._wm_overlay = None

    def _preview_watermark_opacity(self, value: float, respect_visibility: bool = True) -> None:
        if respect_visibility and not self.config_dict.get("show_background", True):
            self._remove_watermark_overlay()
            return
        if not self._wm_scaled_img:
            self._load_watermark_image(respect_visibility=respect_visibility)
        if not self._wm_scaled_img:
            return
        value = max(0.0, min(1.0, float(value)))
        new_img = self._apply_watermark_opacity(self._wm_scaled_img, value)
        self._wm_img = new_img
        self._ensure_watermark_overlay()
        self._position_watermark_overlay()

    def _apply_watermark_opacity(self, img: tk.PhotoImage, opacity: float) -> tk.PhotoImage:
        opacity = max(0.0, min(1.0, float(opacity)))
        try:
            width = img.width()
            height = img.height()
        except Exception:
            return img
        if opacity >= 0.999:
            try:
                return img.copy()
            except Exception:
                return img
        bg_color = "#0b1220"
        try:
            bg_color = self.chat.cget("bg")
        except Exception:
            pass
        bg_rgb = self._hex_to_rgb(bg_color)
        result = tk.PhotoImage(width=width, height=height)
        for y in range(height):
            row_colors = []
            for x in range(width):
                try:
                    pixel = img.get(x, y)
                except Exception:
                    pixel = bg_color
                if not pixel:
                    blended_rgb = bg_rgb
                else:
                    rgb = self._hex_to_rgb(pixel)
                    blended_rgb = (
                        int(rgb[0] * opacity + bg_rgb[0] * (1.0 - opacity)),
                        int(rgb[1] * opacity + bg_rgb[1] * (1.0 - opacity)),
                        int(rgb[2] * opacity + bg_rgb[2] * (1.0 - opacity)),
                    )
                row_colors.append(self._rgb_to_hex(blended_rgb))
            result.put("{" + " ".join(row_colors) + "}", to=(0, y))
        return result

    def _hex_to_rgb(self, value: str) -> tuple[int, int, int]:
        value = (value or "").strip()
        if value.startswith("#") and len(value) == 7:
            try:
                return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))
            except Exception:
                pass
        try:
            r, g, b = self.winfo_rgb(value)
            return r // 256, g // 256, b // 256
        except Exception:
            return 11, 18, 32

    def _rgb_to_hex(self, rgb: tuple[int, int, int]) -> str:
        r, g, b = rgb
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))
        return f"#{r:02x}{g:02x}{b:02x}"


def main() -> None:
    app = JugiAIApp()
    app.mainloop()


if __name__ == "__main__":
    main()

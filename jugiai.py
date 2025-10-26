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

import base64
import json
import mimetypes
import os
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Any, Dict, Generator, List, Optional

import urllib.error
import urllib.request


CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")


DEFAULT_PROFILE_NAME = "AnomFIN · AnomTools"
DEFAULT_PROFILE: Dict[str, Any] = {
    "name": DEFAULT_PROFILE_NAME,
    "model": "gpt-4o-mini",
    "system_prompt": (
        "You are JugiAI, a helpful, concise assistant. "
        "Respond in the user's language by default."
    ),
    "temperature": 0.7,
    "top_p": 1.0,
    "max_tokens": None,
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0,
    "backend": "openai",
}


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
    # Profiilit
    "profiles": {DEFAULT_PROFILE_NAME: DEFAULT_PROFILE},
    "active_profile": DEFAULT_PROFILE_NAME,
    # Mallivaihtoehdot pikanäppäimeen
    "model_options": [
        "gpt-4o-mini",
        "gpt-4.1-mini",
        "gpt-4o",
        "o4-mini",
        "o3-mini",
    ],
}


class JugiAIApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("JugiAI – AnomFIN · AnomTools")
        self.minsize(780, 520)

        self.config_dict = self.load_config()
        self._ensure_profiles()
        self._apply_active_profile()
        self.history: List[Dict[str, str]] = []  # {role:"user"|"assistant", content:str}
        self._wm_img = None
        self._wm_raw_img = None
        self._wm_scaled_img = None
        self._wm_overlay: tk.Label | None = None
        self.llm = None
        self.llm_model_path = None

        self.pending_attachments: List[Dict[str, Any]] = []
        self.stream_start_index: Optional[str] = None
        self.current_stream_text: str = ""
        self.current_stream_timestamp: Optional[str] = None

        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.configure(bg="#020617")
        self.style.configure("TFrame", background="#020617")
        self.style.configure("TLabel", background="#020617", foreground="#e2e8f0")

        self.style.configure("Nav.TFrame", background="#010b1a")
        self.style.configure(
            "Brand.TLabel",
            background="#010b1a",
            foreground="#e0f2fe",
            font=("Segoe UI Semibold", 20, "bold"),
        )
        self.style.configure(
            "NavSubtitle.TLabel",
            background="#010b1a",
            foreground="#94a3b8",
            font=("Segoe UI", 11),
        )
        self.style.configure(
            "Subtle.TLabel",
            background="#020617",
            foreground="#94a3b8",
            font=("Segoe UI", 10),
        )
        self.style.configure(
            "SectionTitle.TLabel",
            background="#020617",
            foreground="#f8fafc",
            font=("Segoe UI Semibold", 15),
        )
        self.style.configure("Surface.TFrame", background="#020617")
        self.style.configure(
            "CardSurface.TFrame",
            background="#0b1220",
            relief=tk.FLAT,
            borderwidth=0,
        )
        self.style.configure(
            "Card.TFrame",
            background="#0f172a",
            relief=tk.FLAT,
            borderwidth=0,
        )
        self.style.configure(
            "Card.TLabel",
            background="#0f172a",
            foreground="#e2e8f0",
        )
        self.style.configure(
            "Attachment.TFrame",
            background="#1e293b",
            relief=tk.FLAT,
            borderwidth=0,
        )
        self.style.configure(
            "Attachment.TLabel",
            background="#1e293b",
            foreground="#f1f5f9",
            font=("Segoe UI", 10),
        )
        self.style.configure(
            "Accent.TButton",
            font=("Segoe UI Semibold", 11),
            padding=10,
            background="#2563eb",
            foreground="#f8fafc",
            borderwidth=0,
        )
        self.style.map(
            "Accent.TButton",
            background=[("pressed", "#1d4ed8"), ("active", "#1d4ed8"), ("disabled", "#1e3a8a")],
            foreground=[("disabled", "#9ca3af")],
        )
        self.style.configure(
            "Toolbar.TButton",
            font=("Segoe UI", 10),
            padding=8,
            background="#0f172a",
            foreground="#e2e8f0",
            borderwidth=0,
        )
        self.style.map(
            "Toolbar.TButton",
            background=[("active", "#172554"), ("pressed", "#1e3a8a")],
            foreground=[("disabled", "#64748b")],
        )
        self.style.configure(
            "StatusBadgeIdle.TLabel",
            background="#10b981",
            foreground="#022c22",
            font=("Segoe UI Semibold", 10),
            padding=(12, 4),
        )
        self.style.configure(
            "StatusBadgeBusy.TLabel",
            background="#f97316",
            foreground="#311303",
            font=("Segoe UI Semibold", 10),
            padding=(12, 4),
        )
        self.style.configure(
            "MetricTitle.TLabel",
            background="#0f172a",
            foreground="#94a3b8",
            font=("Segoe UI", 10),
        )
        self.style.configure(
            "MetricValue.TLabel",
            background="#0f172a",
            foreground="#f8fafc",
            font=("Segoe UI Semibold", 16),
        )
        self.style.configure(
            "TCombobox",
            fieldbackground="#0f172a",
            background="#0f172a",
            foreground="#e2e8f0",
            arrowcolor="#93c5fd",
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", "#0f172a")],
            background=[("readonly", "#0f172a")],
            foreground=[("readonly", "#e2e8f0")],
        )

        self._build_ui()

        # Jos avain puuttuu, avaa asetukset heti
        if not self.config_dict.get("api_key"):
            self.after(200, self.open_settings)

        # Lataa historia ja ikonit/tausta
        self.load_history()
        self._apply_icon_from_config()
        self._load_watermark_image()
        self._insert_watermark_if_needed()
        self.after(1500, self._refresh_ping)

    # --- UI ---
    def _ensure_profiles(self) -> None:
        profiles = self.config_dict.get("profiles")
        if not isinstance(profiles, dict) or not profiles:
            self.config_dict["profiles"] = {DEFAULT_PROFILE_NAME: DEFAULT_PROFILE.copy()}
            profiles = self.config_dict["profiles"]
        else:
            # varmista että jokainen profiili sisältää vähintään nimen
            updated = {}
            for key, value in profiles.items():
                if isinstance(value, dict):
                    v = DEFAULT_PROFILE.copy()
                    v.update(value)
                    if not v.get("name"):
                        v["name"] = key
                    updated[key] = v
            if not updated:
                updated = {DEFAULT_PROFILE_NAME: DEFAULT_PROFILE.copy()}
            self.config_dict["profiles"] = updated
            profiles = updated
        active = self.config_dict.get("active_profile")
        if active not in profiles:
            self.config_dict["active_profile"] = next(iter(profiles.keys()))

    def _apply_active_profile(self) -> None:
        profiles = self.config_dict.get("profiles", {})
        active = self.config_dict.get("active_profile")
        profile = profiles.get(active)
        if not isinstance(profile, dict):
            return
        keys = [
            "model",
            "system_prompt",
            "temperature",
            "top_p",
            "max_tokens",
            "presence_penalty",
            "frequency_penalty",
            "backend",
        ]
        for key in keys:
            if key in profile:
                self.config_dict[key] = profile[key]

    def _apply_profile(self, name: str, persist: bool = True) -> None:
        profiles = self.config_dict.get("profiles", {})
        profile = profiles.get(name)
        if not isinstance(profile, dict):
            return
        keys = [
            "model",
            "system_prompt",
            "temperature",
            "top_p",
            "max_tokens",
            "presence_penalty",
            "frequency_penalty",
            "backend",
        ]
        for key in keys:
            if key in profile:
                self.config_dict[key] = profile[key]
        if persist:
            self.config_dict["active_profile"] = name
            self.save_config()
        self._sync_quick_controls()
        if hasattr(self, "metric_vars"):
            self._update_overview_metrics()

    def _build_ui(self) -> None:
        root = self
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)

        self.typing_status_var = tk.StringVar(value="Valmis")
        self.metric_vars = {
            "profile": tk.StringVar(value=self.config_dict.get("active_profile", DEFAULT_PROFILE_NAME)),
            "model": tk.StringVar(value=self._format_model_label()),
            "messages": tk.StringVar(value="0"),
            "last": tk.StringVar(value="–"),
        }

        header = ttk.Frame(root, style="Nav.TFrame", padding=(24, 20))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=1)
        header.columnconfigure(2, weight=0)

        brand_box = ttk.Frame(header, style="Nav.TFrame")
        brand_box.grid(row=0, column=0, sticky="w")
        ttk.Label(brand_box, text="JugiAI Command Deck", style="Brand.TLabel").pack(anchor="w")
        ttk.Label(
            brand_box,
            text="AnomFIN · Strateginen tekoälytyökalu",
            style="NavSubtitle.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        status_box = ttk.Frame(header, style="Nav.TFrame")
        status_box.grid(row=0, column=1, sticky="w", padx=(24, 0))
        self.ping_canvas = tk.Canvas(
            status_box,
            width=16,
            height=16,
            highlightthickness=0,
            bg="#010b1a",
            bd=0,
        )
        self.ping_canvas.pack(side=tk.LEFT, padx=(0, 8))
        self.ping_indicator = self.ping_canvas.create_oval(2, 2, 14, 14, fill="#f59e0b", outline="")
        self.ping_var = tk.StringVar(value="PING: -- ms")
        ttk.Label(status_box, textvariable=self.ping_var, style="NavSubtitle.TLabel").pack(side=tk.LEFT)

        control_box = ttk.Frame(header, style="Nav.TFrame")
        control_box.grid(row=0, column=2, sticky="e")
        control_box.columnconfigure(1, weight=1)
        self.model_var_quick = tk.StringVar(value=self.config_dict.get("model", "gpt-4o-mini"))
        ttk.Label(control_box, text="Malli:", style="NavSubtitle.TLabel").grid(row=0, column=0, sticky="e")
        model_values = self._resolve_model_options()
        self.model_combo = ttk.Combobox(
            control_box,
            textvariable=self.model_var_quick,
            values=model_values,
            state="readonly",
            width=20,
        )
        self.model_combo.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self.model_combo.bind("<<ComboboxSelected>>", self._on_model_quick_change)

        buttons_bar = ttk.Frame(control_box, style="Nav.TFrame")
        buttons_bar.grid(row=1, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(buttons_bar, text="Profiilit", style="Toolbar.TButton", command=self.open_profiles).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(buttons_bar, text="Tyhjennä", style="Toolbar.TButton", command=self.clear_history).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(buttons_bar, text="Asetukset ⚙", style="Toolbar.TButton", command=self.open_settings).pack(
            side=tk.LEFT
        )

        overview = ttk.Frame(root, style="Surface.TFrame", padding=(24, 12))
        overview.grid(row=1, column=0, sticky="ew")
        for idx in range(4):
            overview.columnconfigure(idx, weight=1)

        metrics = [
            ("Aktiivinen profiili", self.metric_vars["profile"]),
            ("Mallimoottori", self.metric_vars["model"]),
            ("Viestit", self.metric_vars["messages"]),
            ("Viimeisin vastaus", self.metric_vars["last"]),
        ]
        for idx, (title, var) in enumerate(metrics):
            card = tk.Frame(
                overview,
                bg="#0f172a",
                highlightbackground="#1f2937",
                highlightthickness=1,
                bd=0,
                padx=18,
                pady=14,
            )
            card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 12, 0))
            tk.Label(card, text=title, bg="#0f172a", fg="#94a3b8", font=("Segoe UI", 10)).pack(anchor="w")
            tk.Label(
                card,
                textvariable=var,
                bg="#0f172a",
                fg="#f8fafc",
                font=("Segoe UI Semibold", 16),
            ).pack(anchor="w", pady=(4, 0))

        chat_wrapper = ttk.Frame(root, style="Surface.TFrame", padding=(24, 0))
        chat_wrapper.grid(row=2, column=0, sticky="nsew")
        chat_wrapper.rowconfigure(1, weight=1)
        chat_wrapper.columnconfigure(0, weight=1)

        chat_header = ttk.Frame(chat_wrapper, style="Surface.TFrame")
        chat_header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ttk.Label(chat_header, text="Reaaliaikainen keskustelu", style="SectionTitle.TLabel").pack(side=tk.LEFT)
        self.typing_badge = ttk.Label(chat_header, textvariable=self.typing_status_var, style="StatusBadgeIdle.TLabel")
        self.typing_badge.pack(side=tk.RIGHT)

        chat_card = ttk.Frame(chat_wrapper, style="CardSurface.TFrame", padding=0)
        chat_card.grid(row=1, column=0, sticky="nsew")
        chat_card.rowconfigure(0, weight=1)
        chat_card.columnconfigure(0, weight=1)

        text_container = ttk.Frame(chat_card, style="CardSurface.TFrame", padding=18)
        text_container.grid(row=0, column=0, sticky="nsew")
        text_container.rowconfigure(0, weight=1)
        text_container.columnconfigure(0, weight=1)

        self.chat = tk.Text(
            text_container,
            wrap=tk.WORD,
            state=tk.DISABLED,
            yscrollcommand=self._on_chat_scroll,
        )
        self.chat.grid(row=0, column=0, sticky="nsew")

        self._chat_scrollbar = ttk.Scrollbar(text_container, orient=tk.VERTICAL, command=self.chat.yview)
        self._chat_scrollbar.grid(row=0, column=1, sticky="ns", padx=(12, 0))

        try:
            fs = int(self.config_dict.get("font_size", 12))
        except Exception:
            fs = 12

        self.chat.configure(
            bg="#0b1220",
            fg="#f8fafc",
            insertbackground="#f8fafc",
            font=("Segoe UI", fs),
            spacing1=6,
            spacing2=3,
            padx=12,
            pady=12,
            relief=tk.FLAT,
            highlightthickness=0,
        )
        self.chat.bind("<Configure>", lambda event: self._position_watermark_overlay())

        self.chat.tag_configure("role_user", foreground="#93c5fd", font=("Segoe UI", fs))
        self.chat.tag_configure("role_assistant", foreground="#4ade80", font=("Segoe UI", fs))
        self.chat.tag_configure("error", foreground="#f87171", font=("Segoe UI", fs))
        self.chat.tag_configure("header_user", foreground="#bfdbfe", font=("Segoe UI", fs, "bold"))
        self.chat.tag_configure("header_assistant", foreground="#a7f3d0", font=("Segoe UI", fs, "bold"))
        self.chat.tag_configure("attachment", foreground="#facc15", font=("Segoe UI", max(fs - 1, 8)))
        self.chat.tag_configure("separator_user", foreground="#2563eb")
        self.chat.tag_configure("separator_assistant", foreground="#0ea5e9")

        composer = ttk.Frame(root, style="Surface.TFrame", padding=(24, 20))
        composer.grid(row=3, column=0, sticky="ew")
        composer.columnconfigure(0, weight=1)

        attachments_bar = ttk.Frame(composer, style="Surface.TFrame")
        attachments_bar.grid(row=0, column=0, sticky="ew")
        attachments_bar.columnconfigure(1, weight=1)
        ttk.Button(
            attachments_bar,
            text="📎 Liitä tiedosto",
            style="Toolbar.TButton",
            command=self.add_attachment,
        ).grid(row=0, column=0, sticky="w")
        self.attachments_container = ttk.Frame(attachments_bar, style="Surface.TFrame")
        self.attachments_container.grid(row=0, column=1, sticky="ew", padx=(16, 0))

        ttk.Separator(composer, orient=tk.HORIZONTAL).grid(row=1, column=0, sticky="ew", pady=(12, 12))

        self.input = tk.Text(composer, height=5, wrap=tk.WORD, relief=tk.FLAT)
        self.input.grid(row=2, column=0, sticky="ew")
        self.input.configure(
            bg="#111827",
            fg="#f8fafc",
            insertbackground="#f8fafc",
            font=("Segoe UI", fs),
            spacing1=6,
            spacing2=3,
            padx=14,
            pady=14,
            highlightthickness=1,
            highlightcolor="#1f2937",
            highlightbackground="#1f2937",
        )

        action_row = ttk.Frame(composer, style="Surface.TFrame")
        action_row.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        ttk.Label(action_row, text="Vaihto+Enter = rivinvaihto", style="Subtle.TLabel").pack(side=tk.LEFT)
        self.send_btn = ttk.Button(action_row, text="Lähetä ✈️", style="Accent.TButton", command=self.on_send)
        self.send_btn.pack(side=tk.RIGHT)

        self.input.bind("<Shift-Return>", self._newline)
        self.input.bind("<Return>", self._enter_send)

        self._refresh_attachment_chips()
        self._update_overview_metrics()

    def _resolve_model_options(self) -> List[str]:
        options = self.config_dict.get("model_options")
        if isinstance(options, list) and options:
            return [str(o) for o in options]
        return ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "o4-mini", "o3-mini"]

    def _on_model_quick_change(self, event=None) -> None:
        value = self.model_var_quick.get().strip()
        if not value:
            return
        self.config_dict["model"] = value
        profiles = self.config_dict.get("profiles", {})
        active = self.config_dict.get("active_profile")
        if active in profiles and isinstance(profiles[active], dict):
            profiles[active]["model"] = value
        self.save_config()
        self._update_overview_metrics()

    def _sync_quick_controls(self) -> None:
        if hasattr(self, "model_var_quick"):
            self.model_var_quick.set(self.config_dict.get("model", "gpt-4o-mini"))

    def _format_model_label(self) -> str:
        backend = (self.config_dict.get("backend") or "openai").strip().lower()
        if backend == "openai":
            backend_label = "OpenAI"
        elif backend == "local":
            backend_label = "Paikallinen"
        else:
            backend_label = backend.title()
        model = self.config_dict.get("model", DEFAULT_CONFIG["model"])
        return f"{backend_label} · {model}"

    def _update_overview_metrics(self) -> None:
        if not hasattr(self, "metric_vars"):
            return
        self.metric_vars["profile"].set(self.config_dict.get("active_profile", DEFAULT_PROFILE_NAME))
        self.metric_vars["model"].set(self._format_model_label())
        self.metric_vars["messages"].set(str(len(self.history)))
        last_ts = "–"
        for entry in reversed(self.history):
            ts = entry.get("timestamp")
            if ts:
                last_ts = ts
                break
        self.metric_vars["last"].set(last_ts)

    def _refresh_attachment_chips(self) -> None:
        for child in list(self.attachments_container.winfo_children()):
            child.destroy()
        if not self.pending_attachments:
            ttk.Label(
                self.attachments_container,
                text="Ei liitteitä",
                style="Subtle.TLabel",
            ).pack(side=tk.LEFT)
            return
        for idx, att in enumerate(self.pending_attachments):
            chip = ttk.Frame(self.attachments_container, style="Attachment.TFrame", padding=(10, 4))
            chip.pack(side=tk.LEFT, padx=(0, 8))
            name = att.get("name", "liite")
            ttk.Label(chip, text=f"📎 {name}", style="Attachment.TLabel").pack(side=tk.LEFT)
            ttk.Button(
                chip,
                text="✕",
                style="Toolbar.TButton",
                width=2,
                command=lambda i=idx: self.remove_attachment(i),
            ).pack(side=tk.LEFT, padx=(8, 0))

    def add_attachment(self) -> None:
        paths = filedialog.askopenfilenames(title="Valitse liitteet")
        if not paths:
            return
        added = False
        for path in paths:
            try:
                size = os.path.getsize(path)
                with open(path, "rb") as f:
                    data = f.read()
                if size > 4 * 1024 * 1024:
                    if not messagebox.askyesno(
                        "Suuri tiedosto",
                        f"Tiedosto {os.path.basename(path)} on {size} tavua. Lisätäänkö silti?",
                    ):
                        continue
                encoded = base64.b64encode(data).decode("ascii")
                mime, _ = mimetypes.guess_type(path)
                self.pending_attachments.append(
                    {
                        "name": os.path.basename(path),
                        "mime": mime or "tuntematon",
                        "size": size,
                        "data": encoded,
                    }
                )
                added = True
            except Exception as e:
                messagebox.showerror("Liitteen lisäys epäonnistui", str(e))
        if added:
            self._refresh_attachment_chips()

    def remove_attachment(self, index: int) -> None:
        if 0 <= index < len(self.pending_attachments):
            del self.pending_attachments[index]
            self._refresh_attachment_chips()

    def start_assistant_stream(self, timestamp: str) -> None:
        self.current_stream_text = ""
        self.stream_start_index = None
        self.chat.configure(state=tk.NORMAL)
        self.chat.insert(tk.END, "▮ ", ("separator_assistant",))
        self.chat.insert(tk.END, f"JugiAI · {timestamp}\n", ("header_assistant",))
        self.stream_start_index = self.chat.index(tk.END)
        self.chat.insert(tk.END, "JugiAI työskentelee…\n\n", ("role_assistant",))
        self.chat.see(tk.END)
        self.chat.configure(state=tk.DISABLED)

    def update_assistant_stream(self, content: str) -> None:
        if self.stream_start_index is None:
            return
        self.current_stream_text = content
        display = content.strip() or "…"
        self.chat.configure(state=tk.NORMAL)
        self.chat.delete(self.stream_start_index, tk.END)
        self.chat.insert(tk.END, display + "\n\n", ("role_assistant",))
        self.chat.configure(state=tk.DISABLED)
        self.chat.see(tk.END)

    def finalize_assistant_stream(self, content: str) -> None:
        self.update_assistant_stream(content.strip())
        self.stream_start_index = None

    def handle_stream_failure(self, message: str) -> None:
        if self.stream_start_index is not None:
            self.chat.configure(state=tk.NORMAL)
            self.chat.delete(self.stream_start_index, tk.END)
            self.chat.insert(tk.END, f"⚠️ {message}\n\n", ("error",))
            self.chat.configure(state=tk.DISABLED)
            self.chat.see(tk.END)
            self.stream_start_index = None
        else:
            self.append_error(message)

    def _timestamp_now(self) -> str:
        return datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    def _update_ping_indicator(self, latency: Optional[int], state: str) -> None:
        colors = {
            "ok": "#22c55e",
            "warn": "#facc15",
            "error": "#ef4444",
        }
        color = colors.get(state, "#facc15")
        try:
            self.ping_canvas.itemconfig(self.ping_indicator, fill=color)
        except Exception:
            pass
        if state == "ok" and latency is not None:
            self.ping_var.set(f"PING: {latency} ms")
        elif state == "warn" and latency is not None:
            self.ping_var.set(f"PING: {latency} ms (varoitus)")
        else:
            self.ping_var.set("PING: -- ms (ei yhteyttä)")

    def _refresh_ping(self) -> None:
        def worker() -> None:
            api_key = self.config_dict.get("api_key", "").strip()
            url = "https://api.openai.com/v1/models"
            req = urllib.request.Request(url, method="GET")
            if api_key:
                req.add_header("Authorization", f"Bearer {api_key}")
            start = time.time()
            latency: Optional[int] = None
            state = "error"
            try:
                with urllib.request.urlopen(req, timeout=5) as resp:
                    resp.read(1)
                latency = int((time.time() - start) * 1000)
                state = "ok"
            except urllib.error.HTTPError as e:
                latency = int((time.time() - start) * 1000)
                if e.code in (401, 403):
                    state = "warn" if not api_key else "ok"
                else:
                    state = "warn"
            except urllib.error.URLError:
                state = "error"
            except Exception:
                state = "error"
            self.after(0, lambda: self._update_ping_indicator(latency, state))

        threading.Thread(target=worker, daemon=True).start()
        self.after(8000, self._refresh_ping)

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
    def append_message(
        self,
        role: str,
        content: str,
        *,
        timestamp: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        ts = timestamp or self._timestamp_now()
        display_name = "JugiAI" if role == "assistant" else "Sinä"
        header_tag = "header_assistant" if role == "assistant" else "header_user"
        separator_tag = "separator_assistant" if role == "assistant" else "separator_user"
        body_tag = "role_assistant" if role == "assistant" else "role_user"
        content = (content or "").strip()

        self.chat.configure(state=tk.NORMAL)
        self.chat.insert(tk.END, "▮ ", (separator_tag,))
        self.chat.insert(tk.END, f"{display_name} · {ts}\n", (header_tag,))
        if content:
            self.chat.insert(tk.END, content + "\n", (body_tag,))
        if attachments:
            for att in attachments:
                name = att.get("name", "tuntematon")
                mime = att.get("mime", "tiedosto")
                size = att.get("size")
                size_text = f", {size} tavua" if isinstance(size, int) else ""
                self.chat.insert(
                    tk.END,
                    f"   📎 {name} ({mime}{size_text})\n",
                    ("attachment",),
                )
        self.chat.insert(tk.END, "\n")
        self.chat.see(tk.END)
        self.chat.configure(state=tk.DISABLED)
        self._update_overview_metrics()

    def append_error(self, content: str) -> None:
        self.chat.configure(state=tk.NORMAL)
        self.chat.insert(tk.END, "⚠️ Virhe\n", ("error",))
        self.chat.insert(tk.END, content.strip() + "\n\n", ("error",))
        self.chat.see(tk.END)
        self.chat.configure(state=tk.DISABLED)

    # --- Events ---
    def on_send(self) -> None:
        text = self.input.get("1.0", tk.END).strip()
        attachments = [att.copy() for att in self.pending_attachments]
        if not text and not attachments:
            return
        if self.config_dict.get("backend", "openai").lower() == "openai":
            if not self.config_dict.get("api_key"):
                messagebox.showinfo("Asetukset tarvitaan", "Syötä OpenAI API -avain asetuksiin.")
                self.open_settings()
                return

        timestamp = self._timestamp_now()

        # UI-tila ja viestit
        self.input.delete("1.0", tk.END)
        display_text = text if text else "(Liitteet lähetetty)"
        self.append_message("user", display_text, timestamp=timestamp, attachments=attachments)

        history_entry = {
            "role": "user",
            "content": display_text,
            "attachments": attachments,
            "timestamp": timestamp,
        }
        self.history.append(history_entry)
        self.save_history()
        self._update_overview_metrics()

        self.pending_attachments = []
        self._refresh_attachment_chips()

        self.set_busy(True)
        self.current_stream_timestamp = self._timestamp_now()
        self.start_assistant_stream(self.current_stream_timestamp)
        threading.Thread(target=self._worker_call_openai, daemon=True).start()

    def set_busy(self, busy: bool) -> None:
        if busy:
            self.typing_status_var.set("Työstetään pyyntöä…")
            if hasattr(self, "typing_badge"):
                self.typing_badge.configure(style="StatusBadgeBusy.TLabel")
            self.send_btn.configure(state=tk.DISABLED)
        else:
            self.typing_status_var.set("Valmis")
            if hasattr(self, "typing_badge"):
                self.typing_badge.configure(style="StatusBadgeIdle.TLabel")
            self.send_btn.configure(state=tk.NORMAL)

    # --- Model call ---
    def _worker_call_openai(self) -> None:
        accumulated = ""
        try:
            for chunk in self.stream_model_backend():
                if not chunk:
                    continue
                accumulated += chunk
                text_snapshot = accumulated
                self.after(0, lambda t=text_snapshot: self.update_assistant_stream(t))
        except Exception as e:
            msg = str(e)
            self.after(0, lambda m=msg: self.handle_stream_failure(m))
            self.after(0, lambda: self.set_busy(False))
            self.current_stream_timestamp = None
            return

        final_text = accumulated.strip()
        if not final_text:
            final_text = "(Ei vastausta)"
        timestamp = self.current_stream_timestamp or self._timestamp_now()
        history_entry = {
            "role": "assistant",
            "content": final_text,
            "attachments": [],
            "timestamp": timestamp,
        }
        self.history.append(history_entry)
        self.after(0, lambda text=final_text: self.finalize_assistant_stream(text))
        self.after(0, self.save_history)
        self.after(0, self._update_overview_metrics)
        self.after(0, lambda: self.set_busy(False))
        self.current_stream_timestamp = None

    def stream_model_backend(self) -> Generator[str, None, None]:
        backend = (self.config_dict.get("backend", "openai") or "openai").lower()
        if backend == "local":
            yield from self._call_local_llm_stream()
        else:
            yield from self._call_openai_stream()

    def _build_messages_for_backend(self) -> List[Dict[str, Any]]:
        cfg = self.config_dict
        messages: List[Dict[str, Any]] = []
        sys_prompt = (cfg.get("system_prompt") or "").strip()
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})
        for msg in self.history:
            role = msg.get("role", "user")
            messages.append({"role": role, "content": self._compose_message_for_backend(msg)})
        return messages

    def _compose_message_for_backend(self, message: Dict[str, Any]) -> str:
        text = (message.get("content") or "").strip()
        attachments = message.get("attachments") or []
        if not attachments:
            return text
        lines = [text] if text else []
        lines.append("Liitteet (base64-muodossa):")
        for att in attachments:
            name = att.get("name", "liite")
            mime = att.get("mime", "tuntematon")
            size = att.get("size")
            size_info = f", {size} tavua" if isinstance(size, int) else ""
            data = att.get("data", "")
            lines.append(f"{name} ({mime}{size_info})")
            lines.append(f"BASE64:{data}")
        return "\n".join(lines)

    def _call_openai_stream(self) -> Generator[str, None, None]:
        cfg = self.config_dict
        api_key = cfg.get("api_key")
        if not api_key:
            raise RuntimeError("API-avain puuttuu asetuksista.")

        url = "https://api.openai.com/v1/chat/completions"
        payload: Dict[str, Any] = {
            "model": cfg.get("model", "gpt-4o-mini"),
            "messages": self._build_messages_for_backend(),
            "temperature": float(cfg.get("temperature", 0.7)),
            "top_p": float(cfg.get("top_p", 1.0)),
            "presence_penalty": float(cfg.get("presence_penalty", 0.0)),
            "frequency_penalty": float(cfg.get("frequency_penalty", 0.0)),
            "stream": True,
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
                for raw_line in resp:
                    line = raw_line.strip()
                    if not line:
                        continue
                    if not line.startswith(b"data:"):
                        continue
                    chunk_data = line[len(b"data:") :].strip()
                    if not chunk_data or chunk_data == b"[DONE]":
                        if chunk_data == b"[DONE]":
                            break
                        continue
                    try:
                        parsed = json.loads(chunk_data.decode("utf-8"))
                    except Exception:
                        continue
                    choices = parsed.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    text = delta.get("content")
                    if text:
                        yield text
        except urllib.error.HTTPError as e:
            try:
                err_body = e.read().decode("utf-8", errors="ignore")
            except Exception:
                err_body = str(e)
            raise RuntimeError(f"API virhe: {e.code} {err_body}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"Verkkovirhe: {e}") from None

    def _call_local_llm_stream(self) -> Generator[str, None, None]:
        text = self._call_local_llm()
        for chunk in self._chunk_text(text):
            yield chunk

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

        messages = self._build_messages_for_backend()

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
            sys_prompt = (cfg.get("system_prompt") or "").strip()
            user_texts = "\n\n".join(
                [
                    self._compose_message_for_backend(m)
                    for m in self.history
                    if m.get("role") == "user"
                ]
            )
            prompt = (sys_prompt + "\n\n" + user_texts).strip()
            out = self.llm(
                prompt=prompt,
                temperature=float(cfg.get("temperature", 0.7)),
                top_p=float(cfg.get("top_p", 1.0)),
                max_tokens=mt if isinstance(mt, int) and mt > 0 else 256,
            )
            content = out.get("choices", [{}])[0].get("text", "")
        return content or ""

    def _chunk_text(self, text: str, chunk_size: int = 80) -> Generator[str, None, None]:
        buffer = ""
        for char in text:
            buffer += char
            if len(buffer) >= chunk_size and char in ".!?\n ":
                yield buffer
                buffer = ""
        if buffer:
            yield buffer

    # --- Persistence ---
    def load_history(self) -> None:
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self.history = data
                else:
                    self.history = []
                for m in self.history:
                    self.append_message(
                        m.get("role", "user"),
                        m.get("content", ""),
                        timestamp=m.get("timestamp"),
                        attachments=m.get("attachments"),
                    )
            except Exception:
                self.history = []
        self._update_overview_metrics()

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
        self._update_overview_metrics()

    def open_profiles(self) -> None:
        profiles = self.config_dict.get("profiles", {})
        dlg = tk.Toplevel(self)
        dlg.title("Profiilit – JugiAI")
        dlg.transient(self)
        dlg.grab_set()
        dlg.geometry("800x520")

        container = ttk.Frame(dlg, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        list_frame = ttk.Frame(container)
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        ttk.Label(list_frame, text="Profiilit", style="Header.TLabel").pack(anchor="w")
        profile_list = tk.Listbox(list_frame, height=18, exportselection=False)
        profile_list.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        detail = ttk.Frame(container, style="Card.TFrame", padding=12)
        detail.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        name_var = tk.StringVar()
        model_var = tk.StringVar()
        temp_var = tk.DoubleVar()
        top_p_var = tk.DoubleVar()
        max_tokens_var = tk.StringVar()
        presence_var = tk.DoubleVar()
        frequency_var = tk.DoubleVar()
        backend_var = tk.StringVar()

        row = 0
        ttk.Label(detail, text="Nimi", style="Card.TLabel").grid(row=row, column=0, sticky=tk.W)
        ttk.Entry(detail, textvariable=name_var).grid(row=row, column=1, sticky=tk.EW, padx=(8, 0))
        row += 1
        ttk.Label(detail, text="Malli", style="Card.TLabel").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Entry(detail, textvariable=model_var).grid(row=row, column=1, sticky=tk.EW, padx=(8, 0), pady=(8, 0))
        row += 1
        ttk.Label(detail, text="Temperature", style="Card.TLabel").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Spinbox(detail, from_=0.0, to=2.0, increment=0.05, textvariable=temp_var).grid(row=row, column=1, sticky=tk.W, padx=(8, 0), pady=(8, 0))
        row += 1
        ttk.Label(detail, text="top_p", style="Card.TLabel").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Spinbox(detail, from_=0.0, to=1.0, increment=0.05, textvariable=top_p_var).grid(row=row, column=1, sticky=tk.W, padx=(8, 0), pady=(8, 0))
        row += 1
        ttk.Label(detail, text="max_tokens", style="Card.TLabel").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Entry(detail, textvariable=max_tokens_var).grid(row=row, column=1, sticky=tk.EW, padx=(8, 0), pady=(8, 0))
        row += 1
        ttk.Label(detail, text="presence_penalty", style="Card.TLabel").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Spinbox(detail, from_=-2.0, to=2.0, increment=0.1, textvariable=presence_var).grid(row=row, column=1, sticky=tk.W, padx=(8, 0), pady=(8, 0))
        row += 1
        ttk.Label(detail, text="frequency_penalty", style="Card.TLabel").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Spinbox(detail, from_=-2.0, to=2.0, increment=0.1, textvariable=frequency_var).grid(row=row, column=1, sticky=tk.W, padx=(8, 0), pady=(8, 0))
        row += 1
        ttk.Label(detail, text="Backend", style="Card.TLabel").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Combobox(detail, textvariable=backend_var, values=["openai", "local"], state="readonly").grid(row=row, column=1, sticky=tk.W, padx=(8, 0), pady=(8, 0))
        row += 1
        ttk.Label(detail, text="System-prompt", style="Card.TLabel").grid(row=row, column=0, sticky=tk.NW, pady=(8, 0))
        prompt_txt = ScrolledText(detail, height=6, wrap=tk.WORD)
        prompt_txt.grid(row=row, column=1, sticky=tk.NSEW, padx=(8, 0), pady=(8, 0))

        for i in range(2):
            detail.columnconfigure(i, weight=1)
        detail.rowconfigure(row, weight=1)

        profile_names: List[str] = []

        def refresh_list(select_name: Optional[str] = None) -> None:
            profile_list.delete(0, tk.END)
            profile_names.clear()
            active_name = self.config_dict.get("active_profile")
            for name in profiles.keys():
                label = name + (" ★" if name == active_name else "")
                profile_names.append(name)
                profile_list.insert(tk.END, label)
            if select_name and select_name in profiles:
                idx = profile_names.index(select_name)
                profile_list.selection_clear(0, tk.END)
                profile_list.selection_set(idx)
                profile_list.event_generate("<<ListboxSelect>>")

        def load_selected(event=None) -> None:
            selection = profile_list.curselection()
            if not selection:
                return
            name = profile_names[selection[0]]
            data = profiles.get(name, {})
            name_var.set(data.get("name", name))
            model_var.set(data.get("model", self.config_dict.get("model", DEFAULT_CONFIG["model"])))
            temp_var.set(float(data.get("temperature", 0.7)))
            top_p_var.set(float(data.get("top_p", 1.0)))
            mt = data.get("max_tokens")
            max_tokens_var.set(str(int(mt)) if isinstance(mt, int) else "")
            presence_var.set(float(data.get("presence_penalty", 0.0)))
            frequency_var.set(float(data.get("frequency_penalty", 0.0)))
            backend_var.set(data.get("backend", "openai"))
            prompt_txt.delete("1.0", tk.END)
            prompt_txt.insert("1.0", data.get("system_prompt", self.config_dict.get("system_prompt", "")))

        profile_list.bind("<<ListboxSelect>>", load_selected)

        def save_profile(show_info: bool = True) -> Optional[str]:
            selection = profile_list.curselection()
            if not selection:
                if show_info:
                    messagebox.showinfo("Valinta puuttuu", "Valitse profiili listasta.")
                return None
            key = profile_names[selection[0]]
            new_name = name_var.get().strip() or key
            max_tokens_value = max_tokens_var.get().strip()
            profile_data = {
                "name": new_name,
                "model": model_var.get().strip() or self.config_dict.get("model", DEFAULT_CONFIG["model"]),
                "system_prompt": prompt_txt.get("1.0", tk.END).strip() or DEFAULT_PROFILE["system_prompt"],
                "temperature": float(f"{temp_var.get():.3f}"),
                "top_p": float(f"{top_p_var.get():.3f}"),
                "max_tokens": int(max_tokens_value) if max_tokens_value.isdigit() else None,
                "presence_penalty": float(f"{presence_var.get():.3f}"),
                "frequency_penalty": float(f"{frequency_var.get():.3f}"),
                "backend": backend_var.get().strip() or "openai",
            }
            if new_name != key:
                if new_name in profiles:
                    messagebox.showerror("Virhe", "Samanniminen profiili on jo olemassa.")
                    return None
                profiles.pop(key, None)
            profiles[new_name] = profile_data
            if self.config_dict.get("active_profile") == key:
                self.config_dict["active_profile"] = new_name
            self.config_dict["profiles"] = profiles
            self.save_config()
            self._update_overview_metrics()
            if show_info:
                messagebox.showinfo("Tallennettu", f"Profiili '{new_name}' tallennettiin.")
            refresh_list(new_name)
            return new_name

        def activate_profile() -> None:
            name = save_profile(show_info=False)
            if not name:
                return
            self._apply_profile(name, persist=True)
            messagebox.showinfo("Profiili aktivoitu", f"Profiili '{name}' asetettiin oletukseksi.")
            refresh_list(name)

        def apply_profile_once() -> None:
            selection = profile_list.curselection()
            if not selection:
                messagebox.showinfo("Valinta puuttuu", "Valitse profiili listasta.")
                return
            name = profile_names[selection[0]]
            save_profile(show_info=False)
            self._apply_profile(name, persist=False)
            messagebox.showinfo("Profiili ladattu", f"Profiili '{name}' otettiin käyttöön täksi istunnoksi.")

        def new_profile() -> None:
            name = simpledialog.askstring("Uusi profiili", "Anna profiilin nimi:")
            if not name:
                return
            if name in profiles:
                messagebox.showerror("Virhe", "Samanniminen profiili on jo olemassa.")
                return
            profiles[name] = {
                "name": name,
                "model": self.config_dict.get("model", DEFAULT_CONFIG["model"]),
                "system_prompt": self.config_dict.get("system_prompt", DEFAULT_PROFILE["system_prompt"]),
                "temperature": float(self.config_dict.get("temperature", 0.7)),
                "top_p": float(self.config_dict.get("top_p", 1.0)),
                "max_tokens": self.config_dict.get("max_tokens"),
                "presence_penalty": float(self.config_dict.get("presence_penalty", 0.0)),
                "frequency_penalty": float(self.config_dict.get("frequency_penalty", 0.0)),
                "backend": self.config_dict.get("backend", "openai"),
            }
            self.config_dict["profiles"] = profiles
            self.save_config()
            self._update_overview_metrics()
            refresh_list(name)

        def delete_profile() -> None:
            selection = profile_list.curselection()
            if not selection:
                messagebox.showinfo("Valinta puuttuu", "Valitse poistettava profiili.")
                return
            name = profile_names[selection[0]]
            if len(profiles) <= 1:
                messagebox.showinfo("Ei voida poistaa", "Järjestelmä tarvitsee vähintään yhden profiilin.")
                return
            if not messagebox.askyesno("Vahvista", f"Poistetaanko profiili '{name}'?"):
                return
            profiles.pop(name, None)
            self.config_dict["profiles"] = profiles
            if self.config_dict.get("active_profile") == name:
                fallback = next(iter(profiles.keys()))
                self._apply_profile(fallback, persist=True)
            else:
                self.save_config()
                self._update_overview_metrics()
            refresh_list(next(iter(profiles.keys()), None))

        btns = ttk.Frame(dlg, padding=12)
        btns.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(btns, text="Uusi profiili", command=new_profile).pack(side=tk.LEFT)
        ttk.Button(btns, text="Poista", command=delete_profile).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(btns, text="Tallenna muutokset", command=save_profile).pack(side=tk.RIGHT)
        ttk.Button(btns, text="Aktivoi oletukseksi", command=activate_profile).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(btns, text="Lataa tähän istuntoon", command=apply_profile_once).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(btns, text="Sulje", command=dlg.destroy).pack(side=tk.RIGHT, padx=(8, 0))

        refresh_list(self.config_dict.get("active_profile"))
        if not profile_list.curselection() and profile_names:
            profile_list.selection_set(0)
            profile_list.event_generate("<<ListboxSelect>>")

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
        def _bind_scale_readout(var: tk.DoubleVar, target: tk.StringVar, fmt: str = "{:.2f}") -> None:
            def _sync(*_args: Any) -> None:
                try:
                    value = float(var.get())
                except Exception:
                    value = 0.0
                target.set(fmt.format(value))

            var.trace_add("write", _sync)
            _sync()

        ttk.Label(g, text="Temperature (0–2):").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        temp_var = tk.DoubleVar(value=float(self.config_dict.get("temperature", 0.7)))
        ttk.Scale(g, from_=0.0, to=2.0, variable=temp_var).grid(row=row, column=1, sticky=tk.EW, padx=(8, 0), pady=(8, 0))
        temp_readout = tk.StringVar()
        ttk.Label(g, textvariable=temp_readout, style="Subtle.TLabel").grid(
            row=row,
            column=2,
            sticky=tk.W,
            padx=(12, 0),
        )
        _bind_scale_readout(temp_var, temp_readout, "{:.2f}")
        row += 1
        ttk.Label(g, text="Säätelee luovuuden ja satunnaisuuden määrää.", style="Subtle.TLabel").grid(row=row, column=0, columnspan=2, sticky=tk.W)
        row += 1
        ttk.Label(g, text="top_p (0–1):").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        top_p_var = tk.DoubleVar(value=float(self.config_dict.get("top_p", 1.0)))
        ttk.Scale(g, from_=0.0, to=1.0, variable=top_p_var).grid(row=row, column=1, sticky=tk.EW, padx=(8, 0), pady=(8, 0))
        top_p_readout = tk.StringVar()
        ttk.Label(g, textvariable=top_p_readout, style="Subtle.TLabel").grid(
            row=row,
            column=2,
            sticky=tk.W,
            padx=(12, 0),
        )
        _bind_scale_readout(top_p_var, top_p_readout, "{:.2f}")
        row += 1
        ttk.Label(g, text="Rajoittaa todennäköisyysmassaa – pienempi arvo keskittyy varmoihin vastauksiin.", style="Subtle.TLabel").grid(row=row, column=0, columnspan=2, sticky=tk.W)
        row += 1
        ttk.Label(g, text="max_tokens (tyhjä = ei rajaa):").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        mt_var = tk.StringVar(value=str(self.config_dict.get("max_tokens")) if self.config_dict.get("max_tokens") else "")
        ttk.Entry(g, textvariable=mt_var).grid(row=row, column=1, sticky=tk.EW, padx=(8, 0), pady=(8, 0))
        row += 1
        ttk.Label(g, text="Määrittää vastauksen maksimipituuden token-määränä.", style="Subtle.TLabel").grid(row=row, column=0, columnspan=2, sticky=tk.W)
        row += 1
        ttk.Label(g, text="presence_penalty (-2–2):").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        pp_var = tk.DoubleVar(value=float(self.config_dict.get("presence_penalty", 0.0)))
        ttk.Scale(g, from_=-2.0, to=2.0, variable=pp_var).grid(row=row, column=1, sticky=tk.EW, padx=(8, 0), pady=(8, 0))
        pp_readout = tk.StringVar()
        ttk.Label(g, textvariable=pp_readout, style="Subtle.TLabel").grid(
            row=row,
            column=2,
            sticky=tk.W,
            padx=(12, 0),
        )
        _bind_scale_readout(pp_var, pp_readout, "{:+.2f}")
        row += 1
        ttk.Label(g, text="Kannustaa uusiin aiheisiin – suurempi arvo vähentää toistoa.", style="Subtle.TLabel").grid(row=row, column=0, columnspan=2, sticky=tk.W)
        row += 1
        ttk.Label(g, text="frequency_penalty (-2–2):").grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        fp_var = tk.DoubleVar(value=float(self.config_dict.get("frequency_penalty", 0.0)))
        ttk.Scale(g, from_=-2.0, to=2.0, variable=fp_var).grid(row=row, column=1, sticky=tk.EW, padx=(8, 0), pady=(8, 0))
        fp_readout = tk.StringVar()
        ttk.Label(g, textvariable=fp_readout, style="Subtle.TLabel").grid(
            row=row,
            column=2,
            sticky=tk.W,
            padx=(12, 0),
        )
        _bind_scale_readout(fp_var, fp_readout, "{:+.2f}")
        row += 1
        ttk.Label(g, text="Vähentää saman sanan toistumista useita kertoja peräkkäin.", style="Subtle.TLabel").grid(row=row, column=0, columnspan=2, sticky=tk.W)
        row += 1
        for i in range(2):
            g.columnconfigure(i, weight=1)
        g.columnconfigure(2, weight=0)

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
            self._sync_quick_controls()
            self._update_overview_metrics()
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

# -*- coding: utf-8 -*-
"""
JugiAI – yksinkertainen Tkinter-pohjainen chat-sovellus OpenAI:lle.

Ominaisuudet:
- Keskustelu jatkuu niin kauan kuin jatkat (säilyttää session muistissa ajon ajan).
- Asetukset (⚙️): API-avain, malli, system-prompt, temperature, top_p, max_tokens, presence/frequency penalty.
- Ensimmäisellä käynnistyksellä pyytää API-avaimen ja asetukset.

Riippuvuudet: Vain Python 3:n standardikirjastot (tkinter, json, urllib). Ei vaadi asennuksia.
"""

# Windows-native AI. Zero friction, full acceleration.
from __future__ import annotations

import base64
import json
import mimetypes
import os
import sys
import subprocess
import threading
import time
import tkinter as tk
import traceback
from datetime import datetime
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Any, Dict, Generator, List, Optional

import importlib.metadata
import importlib.util
import shutil
import urllib.error
import urllib.request

from playback_utils import (
    MAX_FONT_SIZE,
    MIN_FONT_SIZE,
    clamp_font_size,
    resolve_speed_delay,
)

# Optional: PIL/Pillow support for improved image handling.
try:
    from PIL import Image, ImageEnhance, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")
ERROR_LOG_FILE = os.path.join(os.path.dirname(__file__), "jugiai_error.log")


def _should_redirect_windows_store(executable: str, env: Dict[str, str], platform: str) -> bool:
    if not executable:
        return False
    if env.get("JUGIAI_SKIP_STUB_GUARD") == "1":
        return False
    if not platform.lower().startswith("win"):
        return False
    lower_exec = executable.lower()
    return "windowsapps" in lower_exec and lower_exec.endswith("python.exe")


def _guard_windows_store_stub() -> None:
    if not _should_redirect_windows_store(sys.executable or "", dict(os.environ), sys.platform):
        return

    launcher = shutil.which("py")
    if not launcher:
        return

    env = os.environ.copy()
    env["JUGIAI_SKIP_STUB_GUARD"] = "1"
    script_path = os.path.abspath(__file__)
    args = [launcher, "-3", script_path, *sys.argv[1:]]

    print(
        "Havaittu Windows Storen Python-stubi. Käynnistetään uudelleen komennolla: "
        f"{' '.join(args)}",
        flush=True,
    )

    try:
        subprocess.check_call(args, env=env)
    except Exception as exc:  # pragma: no cover - diagnostiikka
        print(
            "Uudelleenkäynnistys epäonnistui. Käytä komentoa `py -3 jugiai.py`.",
            f"Virhe: {exc}",
            sep="\n",
            file=sys.stderr,
            flush=True,
        )
        return

    raise SystemExit(0)


_guard_windows_store_stub()


def _format_llama_import_error(exc: Exception) -> str:
    python_hint = sys.executable or "python"
    lines = [
        "Paikallista mallia ei voitu alustaa, koska `llama-cpp-python`-kirjaston tuonti epäonnistui.",
        "",
        f"Aktiivinen Python: {python_hint}",
    ]

    spec = importlib.util.find_spec("llama_cpp")
    if spec and getattr(spec, "origin", None):
        lines.append(f"Yritettiin ladata moduuli: {spec.origin}")
    else:
        lines.append("Moduulia `llama_cpp` ei löydy tältä sys.path-polulta.")

    try:
        dist = importlib.metadata.distribution("llama-cpp-python")
    except importlib.metadata.PackageNotFoundError:
        lines.append("llama-cpp-python ei ole asennettuna tähän ympäristöön.")
    except Exception as meta_exc:  # pragma: no cover - diagnostiikka
        lines.append(f"llama-cpp-pythonin metatietojen tarkistus epäonnistui: {meta_exc}")
    else:
        lines.append(f"llama-cpp-python versio: {dist.version}")
        lines.append(f"Asennushakemisto: {dist.locate_file('')}")

    store_stub = "windowsapps" in python_hint.lower()
    suggested_launch: list[str] = []

    if store_stub:
        suggested_launch.append(
            "Nykyinen Python on Windows Storen stubi ilman kirjastoja. Käynnistä JugiAI komennolla "
            "`py -3 jugiai.py` tai käytä `start_jugiai.bat`, jotta oikea ympäristö latautuu."
        )

    venv_python = os.path.join(os.path.dirname(__file__), ".venv", "Scripts", "python.exe")
    if os.path.exists(venv_python):
        suggested_launch.append(
            r"Vaihtoehtoisesti aktivoi virtuaaliympäristö: `\.venv\Scripts\activate` ja aja sitten `python jugiai.py`."
        )

    if suggested_launch:
        lines.extend(["", "Ympäristövinkit:"] + [f"  - {tip}" for tip in suggested_launch])

    lines.extend(
        [
            "",
            "Suositeltu korjaus:",
            f"  \"{python_hint}\" -m pip install --upgrade --prefer-binary llama-cpp-python",
            "",
            f"Alkuperäinen virhe: {exc}",
        ]
    )
    return "\n".join(lines)


def _write_error_log(tb_text: str) -> Optional[str]:
    try:
        with open(ERROR_LOG_FILE, "w", encoding="utf-8") as fh:
            fh.write(tb_text)
        return ERROR_LOG_FILE
    except Exception:  # pragma: no cover - lokitus ei ole kriittinen
        return None


def _show_fatal_error_dialog(summary: str, details: str) -> None:
    dialog_title = "JugiAI – Käynnistysvirhe"
    message = summary
    if details:
        message = f"{summary}\n\n{details}"

    temp_root: Optional[tk.Tk] = None
    try:
        root = tk._default_root  # type: ignore[attr-defined]
        if root is None:
            temp_root = tk.Tk()
            temp_root.withdraw()
            root = temp_root
        messagebox.showerror(dialog_title, message, parent=root)
    except Exception:
        pass
    finally:
        if temp_root is not None:
            try:
                temp_root.destroy()
            except Exception:
                pass


def _handle_fatal_error(exc: BaseException, app: Optional[tk.Tk] = None) -> None:
    if app is not None:
        try:
            app.destroy()
        except Exception:
            pass

    tb_text = traceback.format_exc()
    log_path = _write_error_log(tb_text)
    summary_lines = ["JugiAI pysähtyi odottamattomaan virheeseen."]
    if log_path:
        summary_lines.append(f"Virheloki: {log_path}")
    else:
        summary_lines.append("Virhelokia ei voitu kirjoittaa – tarkista käyttöoikeudet.")

    summary_text = "\n".join(summary_lines)
    details = f"Virhe: {exc}"

    print(summary_text, file=sys.stderr)
    print(tb_text, file=sys.stderr)
    _show_fatal_error_dialog(summary_text, details)

    raise SystemExit(1)


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


def _log_warning(message: str) -> None:
    """Simple console warning logger for watermark and other non-critical errors."""
    print(f"[WARNING] {message}", flush=True)


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
        self.watermark_enabled = True  # Flag to track if watermark loading is available
        self.llm = None
        self.llm_model_path = None
        
        # Logo for messages
        self._msg_logo_img = None
        self._logo_refs: List[Any] = []  # Keep references to prevent garbage collection

        self._is_loading_history = False
        self._history_viewer: Dict[str, Any] | None = None
        self._history_play_job: Optional[str] = None
        self._history_play_speed = "normal"
        self._active_font_size = clamp_font_size(self.config_dict.get("font_size", 12), 0)

        self.pending_attachments: List[Dict[str, Any]] = []
        self.stream_start_index: Optional[str] = None
        self.current_stream_text: str = ""
        self.current_stream_timestamp: Optional[str] = None
        self._is_sending: bool = False

        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        base_bg = "#01030f"
        surface_bg = "#041021"
        card_bg = "#061733"
        accent = "#14f1ff"
        secondary = "#8ddcff"

        self.configure(bg=base_bg)
        self.style.configure("TFrame", background=base_bg)
        self.style.configure("TLabel", background=base_bg, foreground="#e2f7ff")

        self.style.configure("Nav.TFrame", background="#020d21")
        self.style.configure(
            "Brand.TLabel",
            background="#020d21",
            foreground=accent,
            font=("Segoe UI Semibold", 20, "bold"),
        )
        self.style.configure(
            "NavSubtitle.TLabel",
            background="#020d21",
            foreground=secondary,
            font=("Segoe UI", 11),
        )
        self.style.configure(
            "Subtle.TLabel",
            background=base_bg,
            foreground="#6b94b8",
            font=("Segoe UI", 10),
        )
        self.style.configure(
            "SectionTitle.TLabel",
            background=base_bg,
            foreground="#e2f7ff",
            font=("Segoe UI Semibold", 15),
        )
        self.style.configure("Surface.TFrame", background=base_bg)
        self.style.configure(
            "CardSurface.TFrame",
            background=surface_bg,
            relief=tk.FLAT,
            borderwidth=0,
        )
        self.style.configure(
            "Card.TFrame",
            background=card_bg,
            relief=tk.FLAT,
            borderwidth=0,
        )
        self.style.configure(
            "Card.TLabel",
            background=card_bg,
            foreground="#dbeafe",
        )
        self.style.configure(
            "Attachment.TFrame",
            background="#0a2a4f",
            relief=tk.FLAT,
            borderwidth=0,
        )
        self.style.configure(
            "Attachment.TLabel",
            background="#0a2a4f",
            foreground="#f0f9ff",
            font=("Segoe UI", 10),
        )
        self.style.configure(
            "Accent.TButton",
            font=("Segoe UI Semibold", 11),
            padding=10,
            background="#0ea5e9",
            foreground="#0e172a",
            borderwidth=0,
        )
        self.style.map(
            "Accent.TButton",
            background=[("pressed", "#0284c7"), ("active", "#06b6d4"), ("disabled", "#083344")],
            foreground=[("disabled", "#60a5fa")],
        )
        self.style.configure(
            "Toolbar.TButton",
            font=("Segoe UI", 10),
            padding=8,
            background="#071427",
            foreground="#dbeafe",
            borderwidth=0,
        )
        self.style.map(
            "Toolbar.TButton",
            background=[("active", "#0f1e3a"), ("pressed", "#1b3661")],
            foreground=[("disabled", "#3f5670")],
        )
        self.style.configure(
            "StatusBadgeIdle.TLabel",
            background="#15f5d8",
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
            background=card_bg,
            foreground="#60a5fa",
            font=("Segoe UI", 10),
        )
        self.style.configure(
            "MetricValue.TLabel",
            background=card_bg,
            foreground="#e2f7ff",
            font=("Segoe UI Semibold", 16),
        )
        self.style.configure(
            "TCombobox",
            fieldbackground="#041024",
            background="#041024",
            foreground="#dbeafe",
            arrowcolor=accent,
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
        
        # Add smooth scroll animation support
        self._add_smooth_scroll_bindings()
        
        # Add aesthetic enhancements
        self._add_button_hover_effects()

    def _safe_log(self, *args, **kwargs):
        try:
            print("[JugiAI]", *args, **kwargs)
        except Exception:
            pass
    
    def _add_smooth_scroll_bindings(self) -> None:
        """Add smooth scrolling behavior to the chat area."""
        def smooth_scroll(event):
            try:
                # Calculate scroll amount
                delta = -1 if event.delta > 0 else 1
                # Smooth scroll in smaller increments
                for _ in range(3):
                    self.chat.yview_scroll(delta // 3, "units")
                    self.update_idletasks()
                return "break"
            except Exception:
                pass
        
        try:
            self.chat.bind("<MouseWheel>", smooth_scroll)
        except Exception:
            pass
    
    def _add_button_hover_effects(self) -> None:
        """Add subtle hover effects to enhance user experience."""
        def on_enter(event):
            try:
                widget = event.widget
                if isinstance(widget, tk.Widget):
                    # Store original cursor
                    widget._original_cursor = widget.cget("cursor") if hasattr(widget, "cget") else "arrow"
                    widget.configure(cursor="hand2")
            except Exception:
                pass
        
        def on_leave(event):
            try:
                widget = event.widget
                if isinstance(widget, tk.Widget) and hasattr(widget, "_original_cursor"):
                    widget.configure(cursor=widget._original_cursor)
            except Exception:
                pass
        
        # Apply to send button if it exists
        try:
            if hasattr(self, "send_btn"):
                self.send_btn.bind("<Enter>", on_enter)
                self.send_btn.bind("<Leave>", on_leave)
        except Exception:
            pass

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

        header = ttk.Frame(root, style="Nav.TFrame", padding=(16, 12))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=1)
        header.columnconfigure(2, weight=0)

        brand_box = ttk.Frame(header, style="Nav.TFrame")
        brand_box.grid(row=0, column=0, sticky="w")
        ttk.Label(brand_box, text="JugiAI", style="Brand.TLabel").pack(anchor="w")
        ttk.Label(
            brand_box,
            text="AnomFIN · Tekoälytyökalu",
            style="NavSubtitle.TLabel",
        ).pack(anchor="w", pady=(2, 0))

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
        buttons_bar.grid(row=1, column=0, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(buttons_bar, text="Profiilit", style="Toolbar.TButton", command=self.open_profiles).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(buttons_bar, text="Tyhjennä", style="Toolbar.TButton", command=self.clear_history).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(
            buttons_bar,
            text="Tallenteet 🎞️",
            style="Toolbar.TButton",
            command=self.open_history_viewer,
        ).pack(side=tk.LEFT, padx=(0, 6))
        zoom_frame = ttk.Frame(buttons_bar, style="Nav.TFrame")
        zoom_frame.pack(side=tk.LEFT, padx=(2, 6))
        ttk.Label(zoom_frame, text="Zoom", style="NavSubtitle.TLabel").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(
            zoom_frame,
            text="−",
            width=3,
            style="Toolbar.TButton",
            command=lambda: self.adjust_font_size(-1),
        ).pack(side=tk.LEFT)
        ttk.Button(
            zoom_frame,
            text="＋",
            width=3,
            style="Toolbar.TButton",
            command=lambda: self.adjust_font_size(1),
        ).pack(side=tk.LEFT, padx=(4, 0))
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
                highlightbackground="#14f1ff" if idx == 0 else "#1f2937",
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
            bg="#030b1f",
            fg="#e2f7ff",
            insertbackground="#f0f9ff",
            spacing1=6,
            spacing2=3,
            padx=12,
            pady=12,
            relief=tk.FLAT,
            highlightthickness=0,
            borderwidth=0,
        )
        self.chat.bind("<Configure>", lambda event: self._position_watermark_overlay())

        self._apply_font_size(self._active_font_size)

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

        self.input = tk.Text(composer, height=3, wrap=tk.WORD, relief=tk.FLAT)
        self.input.grid(row=2, column=0, sticky="ew")
        self.input.configure(
            bg="#071427",
            fg="#e2f7ff",
            insertbackground="#e2f7ff",
            spacing1=6,
            spacing2=3,
            padx=14,
            pady=14,
            highlightthickness=1,
            highlightcolor="#0ea5e9",
            highlightbackground="#0a223d",
            borderwidth=0,
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
        self._apply_font_size(self._active_font_size)

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

    def _apply_font_size(self, font_size: int) -> None:
        sanitized = clamp_font_size(font_size, 0)
        self._active_font_size = sanitized
        base_font = ("Segoe UI", sanitized)
        accent_font = ("Segoe UI", max(sanitized - 2, MIN_FONT_SIZE - 2, 8))

        if hasattr(self, "chat"):
            try:
                self.chat.configure(font=base_font)
            except Exception:
                pass
            try:
                self.chat.tag_configure("role_user", foreground="#38bdf8", font=base_font)
                self.chat.tag_configure("role_assistant", foreground="#34d399", font=base_font)
                self.chat.tag_configure("error", foreground="#f87171", font=base_font)
                self.chat.tag_configure(
                    "header_user",
                    foreground="#7dd3fc",
                    font=("Segoe UI", sanitized, "bold"),
                )
                self.chat.tag_configure(
                    "header_assistant",
                    foreground="#6ee7b7",
                    font=("Segoe UI", sanitized, "bold"),
                )
                self.chat.tag_configure("attachment", foreground="#facc15", font=accent_font)
                self.chat.tag_configure("separator_user", foreground="#38bdf8")
                self.chat.tag_configure("separator_assistant", foreground="#0ea5e9")
            except Exception:
                pass

        if hasattr(self, "input"):
            try:
                self.input.configure(font=base_font)
            except Exception:
                pass

    def adjust_font_size(self, delta: int) -> None:
        new_size = clamp_font_size(self._active_font_size, delta)
        if new_size == self._active_font_size:
            self._safe_log(f"Font size unchanged at {new_size}")
            return
        self.config_dict["font_size"] = new_size
        self._apply_font_size(new_size)
        self.save_config()

    def _cancel_history_playback_job(self) -> None:
        if self._history_play_job is not None:
            try:
                self.after_cancel(self._history_play_job)
            except Exception:
                pass
            self._history_play_job = None

    def _format_history_entry(self, entry: Dict[str, Any]) -> str:
        timestamp = entry.get("timestamp") or "–"
        role = entry.get("role", "?").upper()
        content = (entry.get("content") or "").strip()
        attachments = entry.get("attachments") or []
        lines = [f"[{timestamp}] {role}"]
        if content:
            lines.append(content)
        if attachments:
            lines.append("Liitteet:")
            for att in attachments:
                name = att.get("name", "liite")
                mime = att.get("mime", "tuntematon")
                size = att.get("size")
                size_info = f" · {size} B" if isinstance(size, int) else ""
                lines.append(f" - {name} ({mime}{size_info})")
        return "\n".join(lines)

    def _refresh_history_viewer(self) -> None:
        viewer = self._history_viewer
        if not viewer:
            return
        window = viewer.get("window")
        if window is None or not window.winfo_exists():
            self._history_viewer = None
            self._cancel_history_playback_job()
            return
        listbox: tk.Listbox = viewer["listbox"]
        selection = listbox.curselection()
        selected_idx = selection[0] if selection else None
        listbox.delete(0, tk.END)
        for idx, entry in enumerate(self.history):
            ts = entry.get("timestamp") or f"{idx + 1:02d}"
            role = entry.get("role", "?").capitalize()
            snippet = (entry.get("content") or "").strip().replace("\n", " ")
            if len(snippet) > 48:
                snippet = snippet[:45] + "…"
            listbox.insert(tk.END, f"{idx + 1:02d}. {ts} · {role} – {snippet}")
        if selected_idx is not None and selected_idx < listbox.size():
            listbox.selection_set(selected_idx)
            listbox.see(selected_idx)
        viewer["status_var"].set(f"Tallenteita: {len(self.history)}")
        state = viewer["state"]
        if state.get("index", 0) > len(self.history):
            state["index"] = len(self.history)

    def _render_history_entry(self, index: int) -> None:
        viewer = self._history_viewer
        if not viewer:
            return
        display: ScrolledText = viewer["display"]
        display.configure(state=tk.NORMAL)
        display.delete("1.0", tk.END)
        if 0 <= index < len(self.history):
            display.insert("1.0", self._format_history_entry(self.history[index]))
        display.configure(state=tk.DISABLED)
        viewer["status_var"].set(f"Tallenteita: {len(self.history)} · Selaus")

    def open_history_viewer(self) -> None:
        viewer = self._history_viewer
        if viewer and viewer.get("window") and viewer["window"].winfo_exists():
            viewer["window"].deiconify()
            viewer["window"].lift()
            viewer["window"].focus_force()
            self._refresh_history_viewer()
            return

        dlg = tk.Toplevel(self)
        dlg.title("Tallenteet – JugiAI")
        dlg.configure(bg="#01030f")
        dlg.geometry("840x540")
        dlg.minsize(760, 480)

        layout = ttk.Frame(dlg, padding=16, style="Surface.TFrame")
        layout.pack(fill=tk.BOTH, expand=True)
        layout.columnconfigure(0, weight=2)
        layout.columnconfigure(1, weight=3)
        layout.rowconfigure(1, weight=1)

        ttk.Label(layout, text="Tallennekirjasto", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(layout, text="Toisto", style="SectionTitle.TLabel").grid(row=0, column=1, sticky="w")

        list_frame = ttk.Frame(layout, style="CardSurface.TFrame", padding=12)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        listbox = tk.Listbox(
            list_frame,
            bg="#041024",
            fg="#e2f7ff",
            highlightcolor="#14f1ff",
            highlightbackground="#0a223d",
            selectbackground="#0ea5e9",
            selectforeground="#01030f",
            activestyle="none",
            relief=tk.FLAT,
        )
        listbox.grid(row=0, column=0, sticky="nsew")
        list_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
        list_scroll.grid(row=0, column=1, sticky="ns")
        listbox.configure(yscrollcommand=list_scroll.set)

        detail_frame = ttk.Frame(layout, style="CardSurface.TFrame", padding=12)
        detail_frame.grid(row=1, column=1, sticky="nsew")
        detail_frame.rowconfigure(0, weight=1)
        detail_frame.columnconfigure(0, weight=1)

        display = ScrolledText(
            detail_frame,
            state=tk.DISABLED,
            wrap=tk.WORD,
            background="#030b1f",
            foreground="#e2f7ff",
            insertbackground="#e2f7ff",
            relief=tk.FLAT,
            highlightthickness=0,
        )
        display.grid(row=0, column=0, sticky="nsew")

        controls = ttk.Frame(detail_frame, style="Surface.TFrame")
        controls.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        controls.columnconfigure(0, weight=1)

        status_var = tk.StringVar(value=f"Tallenteita: {len(self.history)}")
        status_label = ttk.Label(controls, textvariable=status_var, style="Subtle.TLabel")
        status_label.grid(row=0, column=0, sticky="w")

        ttk.Button(controls, text="▶ Toista", style="Toolbar.TButton", command=self.start_history_playback).grid(
            row=0, column=1, padx=(12, 0)
        )
        ttk.Button(controls, text="⏸ Tauko", style="Toolbar.TButton", command=self._pause_history_playback).grid(
            row=0, column=2, padx=(12, 0)
        )
        ttk.Button(controls, text="⏹ Stop", style="Toolbar.TButton", command=self._stop_history_playback).grid(
            row=0, column=3, padx=(12, 0)
        )
        ttk.Button(controls, text="🐢 Hidastus", style="Toolbar.TButton", command=lambda: self._set_history_play_speed("slow")).grid(
            row=0, column=4, padx=(12, 0)
        )
        ttk.Button(controls, text="⚖ Normaali", style="Toolbar.TButton", command=lambda: self._set_history_play_speed("normal")).grid(
            row=0, column=5, padx=(12, 0)
        )
        ttk.Button(controls, text="⚡ Nopeutus", style="Toolbar.TButton", command=lambda: self._set_history_play_speed("fast")).grid(
            row=0, column=6, padx=(12, 0)
        )

        viewer_state = {"index": 0, "speed": self._history_play_speed, "mode": "browse"}
        self._history_viewer = {
            "window": dlg,
            "listbox": listbox,
            "display": display,
            "status_var": status_var,
            "state": viewer_state,
        }

        def _on_select(event=None):
            selection = listbox.curselection()
            if not selection:
                return
            idx = selection[0]
            viewer_state["index"] = idx
            viewer_state["mode"] = "browse"
            self._cancel_history_playback_job()
            self._render_history_entry(idx)

        listbox.bind("<<ListboxSelect>>", _on_select)

        def _close() -> None:
            self._stop_history_playback()
            self._history_viewer = None
            dlg.destroy()

        dlg.protocol("WM_DELETE_WINDOW", _close)
        self._refresh_history_viewer()

    def start_history_playback(self) -> None:
        viewer = self._history_viewer
        if not viewer:
            return
        if not self.history:
            viewer["status_var"].set("Ei tallenteita toistettavaksi")
            return
        listbox: tk.Listbox = viewer["listbox"]
        selection = listbox.curselection()
        start_index = selection[0] if selection else 0
        viewer["state"]["index"] = start_index
        viewer["state"]["mode"] = "play"
        self._cancel_history_playback_job()
        display: ScrolledText = viewer["display"]
        display.configure(state=tk.NORMAL)
        display.delete("1.0", tk.END)
        display.configure(state=tk.DISABLED)
        viewer["status_var"].set(f"Toisto käynnissä ({viewer['state']['speed']})")
        self._history_viewer_play_step()

    def _history_viewer_play_step(self) -> None:
        viewer = self._history_viewer
        if not viewer:
            return
        state = viewer["state"]
        if state.get("mode") != "play":
            return
        idx = state.get("index", 0)
        if idx >= len(self.history):
            self._stop_history_playback(completed=True)
            return
        entry = self.history[idx]
        display: ScrolledText = viewer["display"]
        display.configure(state=tk.NORMAL)
        display.insert(tk.END, self._format_history_entry(entry) + "\n\n")
        display.configure(state=tk.DISABLED)
        display.see(tk.END)
        listbox: tk.Listbox = viewer["listbox"]
        listbox.selection_clear(0, tk.END)
        listbox.selection_set(idx)
        listbox.see(idx)
        state["index"] = idx + 1
        delay = resolve_speed_delay(state.get("speed", "normal"))
        self._history_play_job = self.after(delay, self._history_viewer_play_step)

    def _pause_history_playback(self) -> None:
        viewer = self._history_viewer
        if not viewer:
            return
        self._cancel_history_playback_job()
        viewer["state"]["mode"] = "pause"
        viewer["status_var"].set("Toisto keskeytetty")

    def _stop_history_playback(self, completed: bool = False) -> None:
        viewer = self._history_viewer
        if not viewer:
            return
        self._cancel_history_playback_job()
        viewer["state"].update({"mode": "browse", "index": 0})
        if completed:
            viewer["status_var"].set("Toisto valmis")
        else:
            viewer["status_var"].set(f"Tallenteita: {len(self.history)}")

    def _set_history_play_speed(self, speed: str) -> None:
        viewer = self._history_viewer
        if not viewer:
            return
        normalized = speed if speed in {"slow", "normal", "fast"} else "normal"
        viewer["state"]["speed"] = normalized
        self._history_play_speed = normalized
        if viewer["state"].get("mode") == "play":
            viewer["status_var"].set(f"Toisto käynnissä ({normalized})")
        else:
            viewer["status_var"].set(f"Toistonopeus: {normalized}")

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
        
        # Try to show logo instead of text prefix
        logo_img = self._load_message_logo()
        if logo_img:
            self._logo_refs.append(logo_img)  # Keep reference
            self.chat.image_create(tk.END, image=logo_img)
            self.chat.insert(tk.END, " ", ("separator_assistant",))
        else:
            self.chat.insert(tk.END, "▮ ", ("separator_assistant",))
            
        self.chat.insert(tk.END, f"JugiAI · {timestamp}\n", ("header_assistant",))
        self.stream_start_index = self.chat.index(tk.END)
        self.chat.insert(tk.END, "…\n\n", ("role_assistant",))
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
            # Add subtle pulse animation for "ok" state
            if state == "ok":
                self._animate_ping_pulse()
        except Exception:
            pass
        if state == "ok" and latency is not None:
            self.ping_var.set(f"PING: {latency} ms")
        elif state == "warn" and latency is not None:
            self.ping_var.set(f"PING: {latency} ms (varoitus)")
        else:
            self.ping_var.set("PING: -- ms (ei yhteyttä)")
    
    def _animate_ping_pulse(self, step: int = 0) -> None:
        """Create a subtle pulsing animation for the ping indicator."""
        if step >= 10:
            return  # Animation complete
        
        try:
            # Calculate size variation for pulse effect
            base_size = 2
            max_size = 14
            pulse_range = 2
            
            # Create sine-wave pulse effect
            import math
            angle = (step / 10.0) * math.pi * 2
            size_offset = int(pulse_range * math.sin(angle) / 2)
            
            new_coords = (
                base_size - size_offset,
                base_size - size_offset,
                max_size + size_offset,
                max_size + size_offset
            )
            
            self.ping_canvas.coords(self.ping_indicator, *new_coords)
            
            # Schedule next step
            if step < 9:
                self.after(50, lambda: self._animate_ping_pulse(step + 1))
            else:
                # Reset to original size
                self.ping_canvas.coords(self.ping_indicator, 2, 2, 14, 14)
        except Exception:
            pass

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
        
        # For assistant messages, try to show logo instead of text prefix
        if role == "assistant":
            logo_img = self._load_message_logo()
            if logo_img:
                self._logo_refs.append(logo_img)  # Keep reference
                self.chat.image_create(tk.END, image=logo_img)
                self.chat.insert(tk.END, " ", (separator_tag,))
            else:
                self.chat.insert(tk.END, "▮ ", (separator_tag,))
        else:
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
        if not self._is_loading_history:
            self._update_overview_metrics()
            self._refresh_history_viewer()

    def append_error(self, content: str) -> None:
        self.chat.configure(state=tk.NORMAL)
        self.chat.insert(tk.END, "⚠️ Virhe\n", ("error",))
        self.chat.insert(tk.END, content.strip() + "\n\n", ("error",))
        self.chat.see(tk.END)
        self.chat.configure(state=tk.DISABLED)

    # --- Events ---
    def on_send(self) -> None:
        # Prevent multiple simultaneous sends
        if self._is_sending:
            return
            
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
        self._refresh_history_viewer()

        self.pending_attachments = []
        self._refresh_attachment_chips()

        self._is_sending = True
        self.set_busy(True)
        self.current_stream_timestamp = self._timestamp_now()
        self.start_assistant_stream(self.current_stream_timestamp)
        threading.Thread(target=self._worker_call_openai, daemon=True).start()

    def set_busy(self, busy: bool) -> None:
        if busy:
            self.typing_status_var.set("Työstetään pyyntöä…")
            if hasattr(self, "typing_badge"):
                self.typing_badge.configure(style="StatusBadgeBusy.TLabel")
                # Add a subtle fade/pulse effect
                self._animate_status_badge_change()
            self.send_btn.configure(state=tk.DISABLED)
        else:
            self.typing_status_var.set("Valmis")
            if hasattr(self, "typing_badge"):
                self.typing_badge.configure(style="StatusBadgeIdle.TLabel")
            self.send_btn.configure(state=tk.NORMAL)
    
    def _animate_status_badge_change(self) -> None:
        """Add a subtle animation when the status badge changes."""
        try:
            # Simple flash effect by temporarily modifying relief
            if hasattr(self, "typing_badge"):
                original_style = self.typing_badge.cget("style")
                # This creates a subtle visual feedback
                self.typing_badge.configure(relief=tk.RAISED)
                self.after(100, lambda: self.typing_badge.configure(relief=tk.FLAT) if hasattr(self, "typing_badge") else None)
        except Exception:
            pass

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
            self.after(0, lambda: setattr(self, '_is_sending', False))
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
        self.after(0, self._refresh_history_viewer)
        self.after(0, lambda: self.set_busy(False))
        self.after(0, lambda: setattr(self, '_is_sending', False))
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
        except Exception as exc:
            raise RuntimeError(_format_llama_import_error(exc)) from exc

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
        self._is_loading_history = True
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
        self._is_loading_history = False
        self._update_overview_metrics()
        self._refresh_history_viewer()

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
        self._refresh_history_viewer()

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
    
    def _load_message_logo(self) -> Optional[tk.PhotoImage]:
        """Load and scale the logo for inline message display."""
        path = self._resolve_default_logo()
        if not path or not os.path.exists(path):
            return None
        
        try:
            if PIL_AVAILABLE:
                # Use PIL for better quality scaling
                from PIL import Image, ImageTk
                pil_img = Image.open(path)
                # Scale to approximately 24x24 pixels for inline display
                pil_img.thumbnail((24, 24), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(pil_img)
            else:
                # Fallback to tk.PhotoImage with subsample
                img = tk.PhotoImage(file=path)
                # Subsample to make it smaller (larger number = smaller image)
                return img.subsample(img.width() // 24 + 1, img.height() // 24 + 1)
        except Exception as e:
            _log_warning(f"Failed to load message logo: {e}")
            return None


    def _load_watermark_image(self, respect_visibility: bool = True) -> None:
        """
        Load watermark image with comprehensive error handling.
        If any error occurs, logs a warning and disables watermark instead of crashing.
        """
        self._wm_img = None
        self._wm_raw_img = None
        self._wm_scaled_img = None
        
        if not self.watermark_enabled:
            self._remove_watermark_overlay()
            return
        
        try:
            from PIL import Image
            pil_available = True
        except Exception:
            pil_available = False
            try:
                self._safe_log("Pillow (PIL) is not installed. Watermark disabled. Install Pillow to enable watermark features.")
            except Exception:
                print("[JugiAI] Pillow (PIL) missing; watermark disabled.")
        
        path = self._resolve_default_logo()
        if not path:
            self._remove_watermark_overlay()
            if pil_available:
                try:
                    self._safe_log(f"Watermark file not found at {path!r}; continuing without watermark.")
                except Exception:
                    pass
            return
        
        if not os.path.isfile(path):
            self._remove_watermark_overlay()
            try:
                self._safe_log(f"Watermark file not found at {path!r}; continuing without watermark.")
            except Exception:
                pass
            return
        
        try:
            path = self._resolve_default_logo()
            if not path:
                self._remove_watermark_overlay()
                return
                
            if not os.path.exists(path):
                _log_warning(f"Watermark image file not found: {path}")
                self.watermark_enabled = False
                self._remove_watermark_overlay()
                return
                
            try:
                raw_img = tk.PhotoImage(file=path)
            except tk.TclError as e:
                _log_warning(f"Failed to load watermark image (TclError): {e}")
                self.watermark_enabled = False
                self._remove_watermark_overlay()
                return
            except Exception as e:
                _log_warning(f"Failed to load watermark image: {e}")
                self.watermark_enabled = False
                self._remove_watermark_overlay()
                return
                
            subs = int(self.config_dict.get("background_subsample", 2))
            subs = max(1, min(8, subs))
            try:
                scaled = raw_img.subsample(subs, subs) if subs > 1 else raw_img.copy()
            except Exception as e:
                _log_warning(f"Failed to subsample watermark image: {e}")
                scaled = raw_img
                
            opacity_val = float(self.config_dict.get("background_opacity", DEFAULT_CONFIG["background_opacity"]))
            opacity_val = max(0.0, min(1.0, opacity_val))
            
            try:
                processed = self._apply_watermark_opacity(scaled, opacity_val)
            except Exception as e:
                _log_warning(f"Failed to apply watermark opacity: {e}")
                processed = scaled
                
            self._wm_raw_img = raw_img
            self._wm_scaled_img = scaled
            self._wm_img = processed
            
        except Exception as e:
            _log_warning(f"Unexpected error loading watermark, continuing without it: {e}")
            self.watermark_enabled = False
            self._wm_img = None
            self._wm_raw_img = None
            self._wm_scaled_img = None
            self._remove_watermark_overlay()
            try:
                self._safe_log("Failed to load/process watermark; continuing without watermark.")
                self._safe_log(traceback.format_exc())
            except Exception:
                pass
            return
        
        try:
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
        except Exception:
            self._remove_watermark_overlay()
            try:
                self._safe_log("Failed to load/process watermark; continuing without watermark.")
                self._safe_log(traceback.format_exc())
            except Exception:
                pass
            return

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
        """
        Apply an opacity factor to a tk.PhotoImage.
        Uses PIL/Pillow for better performance and reliability when available,
        otherwise falls back to pixel-by-pixel manipulation.
        - img: tk.PhotoImage
        - opacity: numeric or string representing 0..1 (or 0..100 as percent)
        Returns a tk.PhotoImage with opacity applied.
        """
        # Normalize opacity to float 0..1
        try:
            normalized_opacity = float(opacity)
        except Exception:
            # If someone passed "50" meaning 50%, normalize
            try:
                normalized_opacity = float(str(opacity).strip().rstrip("%")) / 100.0
            except Exception:
                normalized_opacity = 1.0

        # If user gave 0..100 scale, convert
        if normalized_opacity > 1.0:
            normalized_opacity = max(0.0, min(100.0, normalized_opacity)) / 100.0

        opacity_val = max(0.0, min(1.0, normalized_opacity))

        # If opacity is essentially 1.0, just return a copy
        if opacity_val >= 0.999:
            try:
                return img.copy()
            except Exception as e:
                _log_warning(f"Failed to copy image: {e}")
                return img

        # Try PIL/Pillow approach for better performance
        if PIL_AVAILABLE:
            try:
                # Convert tk.PhotoImage to PIL Image
                # Get dimensions
                width = img.width()
                height = img.height()
                
                # Create a PIL image from tk.PhotoImage pixel data
                # We need to get the data in a format PIL can use
                pil_img = Image.new('RGBA', (width, height))
                pixels = []
                for y in range(height):
                    for x in range(width):
                        try:
                            pixel = img.get(x, y)
                        except Exception:
                            pixel = None
                        if pixel:
                            rgb = self._hex_to_rgb(pixel)
                            pixels.append(rgb + (255,))  # Add full alpha
                        else:
                            pixels.append((11, 18, 32, 255))
                pil_img.putdata(pixels)
                
                # Apply opacity by modifying alpha channel
                r, g, b, a = pil_img.split()
                a = a.point(lambda v: int(v * opacity_val))
                pil_img = Image.merge('RGBA', (r, g, b, a))
                
                # Convert back to tk.PhotoImage
                return ImageTk.PhotoImage(pil_img)
            except Exception:
                # Fall through to fallback implementation
                pass

        # Fallback: pixel-by-pixel manipulation (original implementation)
        try:
            width = img.width()
            height = img.height()
        except Exception:
            return img
            
        bg_color = "#0b1220"
        try:
            bg_color = self.chat.cget("bg")
        except Exception:
            pass
            
        bg_rgb = self._hex_to_rgb(bg_color)
        opacity_scalar = opacity_val
        result = tk.PhotoImage(width=width, height=height)
        for y in range(height):
            row_colors = []
            for x in range(width):
                try:
                    pixel = img.get(x, y)
                except Exception:
                    pixel = None
                if not pixel:
                    blended_rgb = bg_rgb
                else:
                    rgb = self._hex_to_rgb(pixel)
                    blended_rgb = (
                        int(rgb[0] * opacity_scalar + bg_rgb[0] * (1.0 - opacity_scalar)),
                        int(rgb[1] * opacity_scalar + bg_rgb[1] * (1.0 - opacity_scalar)),
                        int(rgb[2] * opacity_scalar + bg_rgb[2] * (1.0 - opacity_scalar)),
                    )
                row_colors.append(self._rgb_to_hex(blended_rgb))
            result.put("{" + " ".join(row_colors) + "}", to=(0, y))
        return result

    def _hex_to_rgb(self, value: str | tuple | list) -> tuple[int, int, int]:
        """
        Convert a color value to an (r, g, b) tuple (0..255).
        Accepts:
          - tuple/list: (r,g,b) or (r,g,b,a) -> uses first three elements
          - hex string: '#RRGGBB', 'RRGGBB', '#RGB', 'RGB'
          - numeric/other strings: attempts conversion via str()
        Returns a default dark blue (11, 18, 32) for invalid inputs.
        """
        # If tuple/list already, take first 3 numeric components
        if isinstance(value, (tuple, list)):
            if len(value) < 3:
                return (11, 18, 32)
            try:
                r, g, b = int(value[0]), int(value[1]), int(value[2])
                return (r, g, b)
            except Exception:
                return (11, 18, 32)

        # None check
        if value is None:
            return (11, 18, 32)

        s = str(value).strip()
        if not s:
            return (11, 18, 32)
            
        if s.startswith('#'):
            s = s[1:]

        # Short-hand rgb e.g. 'f0a' -> 'ff00aa'
        if len(s) == 3:
            s = ''.join(ch * 2 for ch in s)

        if len(s) != 6:
            # Try winfo_rgb as fallback for named colors
            try:
                r, g, b = self.winfo_rgb(value)
                return r // 256, g // 256, b // 256
            except Exception:
                return (11, 18, 32)

        try:
            r = int(s[0:2], 16)
            g = int(s[2:4], 16)
            b = int(s[4:6], 16)
            return (r, g, b)
        except Exception:
            return (11, 18, 32)

    def _rgb_to_hex(self, rgb: tuple[int, int, int]) -> str:
        r, g, b = rgb
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))
        return f"#{r:02x}{g:02x}{b:02x}"


def main() -> None:
    app: Optional[JugiAIApp] = None
    try:
        app = JugiAIApp()
        app.mainloop()
    except Exception as exc:
        _handle_fatal_error(exc, app)


if __name__ == "__main__":
    main()

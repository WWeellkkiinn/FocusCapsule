from __future__ import annotations

import customtkinter as ctk

from focuscapsule.state import SessionConfig


def format_countdown(seconds: int) -> str:
    minutes, secs = divmod(max(0, int(seconds)), 60)
    return f"{minutes:02d}:{secs:02d}"


def format_minutes_preview(value: str, fallback_minutes: int = 25) -> str:
    try:
        minutes = max(0, int(value.strip()))
    except (TypeError, ValueError, AttributeError):
        minutes = fallback_minutes
    return format_countdown(minutes * 60)


def compute_progress_ratio(remaining_sec: int, total_sec: int) -> float:
    if total_sec <= 0:
        return 1.0
    return max(0.0, min(1.0, 1 - remaining_sec / total_sec))


def normalize_start_mode(value: str) -> str:
    return "capsule" if value == "capsule" else "main"


class MainSettingsWindow(ctk.CTk):
    def __init__(self, on_start, on_switch_to_capsule=None, on_end_session=None) -> None:
        super().__init__()
        self.title("FocusCapsule")
        self.geometry("440x520")
        self.resizable(False, False)
        self.configure(fg_color="#FFFFFF")
        self.on_start = on_start
        self.on_switch_to_capsule = on_switch_to_capsule
        self.on_end_session = on_end_session

        self.total_minutes_var = ctk.StringVar(value="25")
        self.interval_min_var = ctk.StringVar(value="3")
        self.interval_max_var = ctk.StringVar(value="5")
        self.break_seconds_var = ctk.StringVar(value="10")
        self.sound_var = ctk.BooleanVar(value=True)
        self.seed_var = ctk.StringVar(value="")
        self.capsule_mode_var = ctk.BooleanVar(value=False)
        self.error_var = ctk.StringVar(value="")
        self.session_hint_var = ctk.StringVar(value="准备开始专注")
        self.countdown_var = ctk.StringVar(value="25:00")

        self._build()
        self._bind_preview_updates()
        self.show_config_view()

    def _build(self) -> None:
        self.container = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=16,
            border_width=0,
        )
        self.container.pack(fill="both", expand=True, padx=18, pady=18)

        self.config_frame = ctk.CTkFrame(
            self.container,
            fg_color="#FFFFFF",
            corner_radius=16,
            border_width=0,
        )
        self.session_frame = ctk.CTkFrame(
            self.container,
            fg_color="#FFFFFF",
            corner_radius=16,
            border_width=0,
        )

        self._build_config_view()
        self._build_session_view()

    def _create_countdown_card(self, master, subtitle_var=None) -> ctk.CTkProgressBar:
        card = ctk.CTkFrame(
            master,
            fg_color="#F8FAFC",
            border_color="#D7DEE8",
            border_width=1,
            corner_radius=18,
        )
        card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            card,
            text="专注倒计时",
            font=("Microsoft YaHei", 14),
            text_color="#243447",
        ).pack(pady=(14, 0))
        ctk.CTkLabel(
            card,
            textvariable=self.countdown_var,
            font=("Consolas", 36),
            text_color="#0F172A",
        ).pack(pady=(0, 4))
        if subtitle_var is not None:
            ctk.CTkLabel(
                card,
                textvariable=subtitle_var,
                font=("Microsoft YaHei", 12),
                text_color="#526072",
            ).pack(pady=(0, 10))
            progress_pady = (0, 14)
        else:
            progress_pady = (8, 14)

        progress = ctk.CTkProgressBar(card)
        progress.configure(
            fg_color="#E5EAF2",
            progress_color="#3B82F6",
            border_color="#C9D4E3",
            border_width=1,
        )
        progress.set(0)
        progress.pack(fill="x", padx=16, pady=progress_pady)
        return progress

    def _build_config_view(self) -> None:
        self.preview_progress = self._create_countdown_card(self.config_frame)

        form_card = ctk.CTkFrame(
            self.config_frame,
            fg_color="#FFFFFF",
            border_color="#E5EAF2",
            border_width=1,
            corner_radius=18,
        )
        form_card.pack(fill="x", pady=(0, 14))

        fields = [
            ("专注总时长(分钟)", self.total_minutes_var),
            ("随机区间最小值(分钟)", self.interval_min_var),
            ("随机区间最大值(分钟)", self.interval_max_var),
            ("休息时长(秒)", self.break_seconds_var),
            ("随机种子(可选)", self.seed_var),
        ]

        for idx, (label, var) in enumerate(fields):
            ctk.CTkLabel(form_card, text=label, text_color="#243447").grid(
                row=idx, column=0, sticky="w", pady=(10, 4), padx=(16, 10)
            )
            ctk.CTkEntry(
                form_card,
                textvariable=var,
                width=220,
                fg_color="#FFFFFF",
                border_color="#C9D4E3",
                text_color="#0F172A",
            ).grid(row=idx, column=1, sticky="ew", pady=(10, 4), padx=(0, 16))

        ctk.CTkSwitch(
            form_card,
            text="声音提示",
            variable=self.sound_var,
            text_color="#243447",
        ).grid(row=len(fields), column=0, columnspan=2, sticky="w", pady=(12, 12), padx=16)
        ctk.CTkSwitch(
            form_card,
            text="胶囊模式",
            variable=self.capsule_mode_var,
            text_color="#243447",
        ).grid(row=len(fields) + 1, column=0, columnspan=2, sticky="w", pady=(0, 12), padx=16)
        form_card.columnconfigure(1, weight=1)

        action_card = ctk.CTkFrame(
            self.config_frame,
            fg_color="#FFFFFF",
            border_color="#E5EAF2",
            border_width=1,
            corner_radius=18,
        )
        action_card.pack(fill="x")

        ctk.CTkButton(action_card, text="开始专注", command=self._on_start_clicked).pack(
            fill="x", padx=16, pady=(14, 8)
        )
        ctk.CTkLabel(action_card, textvariable=self.error_var, text_color="#ff6b6b").pack(
            anchor="w", padx=16, pady=(0, 14)
        )

    def _build_session_view(self) -> None:
        self.session_progress = self._create_countdown_card(self.session_frame, self.session_hint_var)

        action_card = ctk.CTkFrame(
            self.session_frame,
            fg_color="#FFFFFF",
            border_color="#E5EAF2",
            border_width=1,
            corner_radius=18,
        )
        action_card.pack(fill="x")

        self.switch_mode_button = ctk.CTkButton(
            action_card,
            text="切换到胶囊模式",
            command=self._on_switch_to_capsule_clicked,
        )
        self.switch_mode_button.pack(fill="x", padx=16, pady=(14, 8))

        self.end_session_button = ctk.CTkButton(
            action_card,
            text="结束专注",
            fg_color="#E2E8F0",
            hover_color="#CBD5E1",
            text_color="#0F172A",
            command=self._on_end_session_clicked,
        )
        self.end_session_button.pack(fill="x", padx=16, pady=(0, 14))

    def _bind_preview_updates(self) -> None:
        self.total_minutes_var.trace_add("write", self._on_total_minutes_changed)
        self._update_preview_countdown()

    def _show_view(self, view: ctk.CTkFrame) -> None:
        self.config_frame.pack_forget()
        self.session_frame.pack_forget()
        view.pack(fill="both", expand=True)

    def _on_total_minutes_changed(self, *_args) -> None:
        self._update_preview_countdown()

    def _update_preview_countdown(self) -> None:
        self.countdown_var.set(format_minutes_preview(self.total_minutes_var.get()))
        self.preview_progress.set(0)

    def _on_start_clicked(self) -> None:
        try:
            seed = self.seed_var.get().strip()
            seed_val = int(seed) if seed else None
            config = SessionConfig(
                total_minutes=int(self.total_minutes_var.get().strip()),
                interval_min_minutes=float(self.interval_min_var.get().strip()),
                interval_max_minutes=float(self.interval_max_var.get().strip()),
                break_seconds=int(self.break_seconds_var.get().strip()),
                sound_enabled=bool(self.sound_var.get()),
                seed=seed_val,
                start_mode="capsule" if bool(self.capsule_mode_var.get()) else "main",
            )
        except ValueError:
            self.error_var.set("请输入合法数字")
            return
        self.error_var.set("")
        self.on_start(config)

    def _on_switch_to_capsule_clicked(self) -> None:
        if callable(self.on_switch_to_capsule):
            self.on_switch_to_capsule()

    def _on_end_session_clicked(self) -> None:
        if callable(self.on_end_session):
            self.on_end_session()

    def set_form(self, config: SessionConfig) -> None:
        self.total_minutes_var.set(str(config.total_minutes))
        self.interval_min_var.set(str(config.interval_min_minutes))
        self.interval_max_var.set(str(config.interval_max_minutes))
        self.break_seconds_var.set(str(config.break_seconds))
        self.sound_var.set(config.sound_enabled)
        self.seed_var.set("" if config.seed is None else str(config.seed))
        self.capsule_mode_var.set(normalize_start_mode(config.start_mode) == "capsule")
        self._update_preview_countdown()

    def show_error(self, text: str) -> None:
        self.error_var.set(text)

    def show_config_view(self) -> None:
        self.session_hint_var.set("准备开始专注")
        self._update_preview_countdown()
        self._show_view(self.config_frame)

    def show_session_view(self) -> None:
        self._show_view(self.session_frame)

    def update_session_view(
        self,
        remaining_sec: int,
        total_sec: int,
        status_text: str = "当前正在专注，请保持节奏。",
        switch_enabled: bool = True,
    ) -> None:
        self.session_hint_var.set(status_text)
        self.countdown_var.set(format_countdown(remaining_sec))
        self.session_progress.set(compute_progress_ratio(remaining_sec, total_sec))
        self.switch_mode_button.configure(state="normal" if switch_enabled else "disabled")

from __future__ import annotations

import customtkinter as ctk

from focuscapsule.state import SessionConfig

WINDOW_WIDTH = 404
WINDOW_HEIGHT = 392
SHORT_INPUT_WIDTH = 62


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


def compute_center_position(
    screen_width: int,
    screen_height: int,
    window_width: int,
    window_height: int,
) -> tuple[int, int]:
    x = max(0, (int(screen_width) - int(window_width)) // 2)
    y = max(0, (int(screen_height) - int(window_height)) // 2)
    return x, y


def compute_window_outer_size(
    client_width: int,
    client_height: int,
    frame_width: int,
    titlebar_height: int,
) -> tuple[int, int]:
    outer_width = int(client_width) + max(0, int(frame_width) * 2)
    outer_height = int(client_height) + max(0, int(frame_width)) + max(0, int(titlebar_height))
    return outer_width, outer_height


class MainSettingsWindow(ctk.CTk):
    def __init__(
        self,
        on_start,
        on_switch_to_capsule=None,
        on_end_session=None,
        on_start_mode_change=None,
    ) -> None:
        super().__init__()
        self.title("FocusCapsule")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.resizable(False, False)
        self.configure(fg_color="#FFFFFF")
        self.on_start = on_start
        self.on_switch_to_capsule = on_switch_to_capsule
        self.on_end_session = on_end_session
        self.on_start_mode_change = on_start_mode_change

        self.total_minutes_var = ctk.StringVar(value="25")
        self.interval_min_var = ctk.StringVar(value="3")
        self.interval_max_var = ctk.StringVar(value="5")
        self.break_seconds_var = ctk.StringVar(value="10")
        self.finish_break_minutes_var = ctk.StringVar(value="5")
        self.sound_var = ctk.BooleanVar(value=True)
        self.capsule_mode_var = ctk.BooleanVar(value=False)
        self.error_var = ctk.StringVar(value="")
        self.session_hint_var = ctk.StringVar(value="当前正在专注，请保持节奏。")
        self.countdown_var = ctk.StringVar(value="25:00")
        self._error_label: ctk.CTkLabel | None = None

        self._build()
        self._center_on_screen()
        self._bind_preview_updates()
        self.show_config_view()

    def _center_on_screen(self) -> None:
        self.update_idletasks()
        frame_width = self.winfo_rootx() - self.winfo_x()
        titlebar_height = self.winfo_rooty() - self.winfo_y()
        outer_width, outer_height = compute_window_outer_size(
            client_width=self.winfo_width(),
            client_height=self.winfo_height(),
            frame_width=frame_width,
            titlebar_height=titlebar_height,
        )
        x, y = compute_center_position(
            screen_width=self.winfo_screenwidth(),
            screen_height=self.winfo_screenheight(),
            window_width=outer_width,
            window_height=outer_height,
        )
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

    def _build(self) -> None:
        self.container = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=0,
            border_width=0,
        )
        self.container.pack(fill="both", expand=True, padx=14, pady=12)

        self.config_frame = ctk.CTkFrame(
            self.container,
            fg_color="#FFFFFF",
            border_width=0,
        )
        self.session_frame = ctk.CTkFrame(
            self.container,
            fg_color="#FFFFFF",
            border_width=0,
        )

        self._build_config_view()
        self._build_session_view()

    def _create_countdown_card(self, master) -> ctk.CTkProgressBar:
        card = ctk.CTkFrame(
            master,
            fg_color="#F6F8FB",
            border_color="#D7DEE8",
            border_width=1,
            corner_radius=18,
            height=108,
        )
        card.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            card,
            textvariable=self.countdown_var,
            font=("Consolas", 34),
            text_color="#0F172A",
        ).pack(expand=True, pady=(12, 6))

        progress = ctk.CTkProgressBar(card, height=10)
        progress.configure(
            fg_color="#E5EAF2",
            progress_color="#3B82F6",
            border_color="#C9D4E3",
            border_width=1,
        )
        progress.set(0)
        progress.pack(fill="x", padx=16, pady=(0, 12))
        return progress

    def _create_panel(self, master, height: int | None = None) -> ctk.CTkFrame:
        panel_kwargs = {
            "fg_color": "#FFFFFF",
            "border_color": "#E5EAF2",
            "border_width": 1,
            "corner_radius": 18,
        }
        if height is not None:
            panel_kwargs["height"] = height
        panel = ctk.CTkFrame(master, **panel_kwargs)
        panel.pack(fill="x", pady=(0, 8))
        return panel

    def _create_short_entry(self, master, variable: ctk.StringVar) -> ctk.CTkEntry:
        return ctk.CTkEntry(
            master,
            textvariable=variable,
            width=SHORT_INPUT_WIDTH,
            height=32,
            justify="center",
            fg_color="#FFFFFF",
            border_color="#C9D4E3",
            text_color="#0F172A",
        )

    def _build_compact_field_panel(self) -> ctk.CTkFrame:
        panel = self._create_panel(self.config_frame)
        top_row = ctk.CTkFrame(panel, fg_color="transparent")
        top_row.pack(fill="x", padx=14, pady=(10, 6))
        top_row.grid_columnconfigure(1, weight=1)
        top_row.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(top_row, text="专注时长", text_color="#243447").grid(
            row=0, column=0, sticky="w"
        )
        duration_row = ctk.CTkFrame(top_row, fg_color="transparent")
        duration_row.grid(row=0, column=1, sticky="w", padx=(8, 18))
        self._create_short_entry(duration_row, self.total_minutes_var).pack(side="left")
        ctk.CTkLabel(duration_row, text="分钟", text_color="#526072").pack(side="left", padx=(8, 0))

        ctk.CTkLabel(top_row, text="休息时长", text_color="#243447").grid(
            row=0, column=2, sticky="w"
        )
        break_row = ctk.CTkFrame(top_row, fg_color="transparent")
        break_row.grid(row=0, column=3, sticky="w", padx=(8, 0))
        self._create_short_entry(break_row, self.break_seconds_var).pack(side="left")
        ctk.CTkLabel(break_row, text="秒", text_color="#526072").pack(side="left", padx=(8, 0))

        bottom_row = ctk.CTkFrame(panel, fg_color="transparent")
        bottom_row.pack(fill="x", padx=14, pady=(0, 10))
        ctk.CTkLabel(bottom_row, text="随机区间", text_color="#243447").pack(side="left")
        interval_row = ctk.CTkFrame(bottom_row, fg_color="transparent")
        interval_row.pack(side="left", padx=(8, 0))
        self._create_short_entry(interval_row, self.interval_min_var).pack(side="left")
        ctk.CTkLabel(interval_row, text="~", text_color="#526072").pack(side="left", padx=8)
        self._create_short_entry(interval_row, self.interval_max_var).pack(side="left")
        ctk.CTkLabel(interval_row, text="分钟", text_color="#526072").pack(side="left", padx=(8, 0))

        finish_break_row = ctk.CTkFrame(panel, fg_color="transparent")
        finish_break_row.pack(fill="x", padx=14, pady=(0, 10))
        ctk.CTkLabel(finish_break_row, text="结束后休息", text_color="#243447").pack(side="left")
        finish_row = ctk.CTkFrame(finish_break_row, fg_color="transparent")
        finish_row.pack(side="left", padx=(8, 0))
        self._create_short_entry(finish_row, self.finish_break_minutes_var).pack(side="left")
        ctk.CTkLabel(finish_row, text="分钟", text_color="#526072").pack(side="left", padx=(8, 0))
        return panel

    def _build_toggle_panel(self) -> ctk.CTkFrame:
        panel = self._create_panel(self.config_frame)
        switch_row = ctk.CTkFrame(panel, fg_color="transparent")
        switch_row.pack(fill="x", padx=10, pady=8)

        ctk.CTkSwitch(
            switch_row,
            text="声音提示",
            variable=self.sound_var,
            text_color="#243447",
        ).pack(side="left", padx=(4, 14))
        ctk.CTkSwitch(
            switch_row,
            text="胶囊模式",
            variable=self.capsule_mode_var,
            text_color="#243447",
            command=self._emit_capsule_mode_change,
        ).pack(side="left")
        return panel

    def _build_status_panel(self, master, text_var: ctk.StringVar, text_color: str = "#526072") -> ctk.CTkFrame:
        panel = self._create_panel(master, height=74)
        ctk.CTkLabel(
            panel,
            textvariable=text_var,
            text_color=text_color,
            justify="left",
            wraplength=344,
        ).pack(fill="x", padx=16, pady=(14, 14))
        return panel

    def _build_action_panel(
        self,
        master,
        button_specs: list[dict],
        error_var=None,
        height: int | None = None,
    ) -> ctk.CTkFrame:
        panel = self._create_panel(master, height=height)
        for idx, spec in enumerate(button_specs):
            pady = (12, 8) if idx == 0 else (0, 8)
            if idx == len(button_specs) - 1:
                pady = (pady[0], 12)
            button_kwargs = {
                "text": spec["text"],
                "command": spec["command"],
                "height": 34,
            }
            for key in ("fg_color", "hover_color", "text_color"):
                if key in spec:
                    button_kwargs[key] = spec[key]
            button = ctk.CTkButton(panel, **button_kwargs)
            button.pack(fill="x", padx=14, pady=pady)
            spec["widget_ref"][0] = button

        if error_var is not None:
            self._error_label = ctk.CTkLabel(
                panel,
                textvariable=error_var,
                text_color="#ff6b6b",
                anchor="w",
                justify="left",
                wraplength=344,
            )
            error_var.trace_add("write", self._on_error_text_changed)
            self._toggle_error_label(error_var.get())
        return panel

    def _toggle_error_label(self, text: str) -> None:
        if self._error_label is None:
            return
        if text.strip():
            if not self._error_label.winfo_manager():
                self._error_label.pack(fill="x", padx=14, pady=(0, 10))
        elif self._error_label.winfo_manager():
            self._error_label.pack_forget()

    def _on_error_text_changed(self, *_args) -> None:
        self._toggle_error_label(self.error_var.get())

    def _build_config_view(self) -> None:
        self.preview_progress = self._create_countdown_card(self.config_frame)
        self._build_compact_field_panel()
        self._build_toggle_panel()

        start_button_ref = [None]
        self._build_action_panel(
            self.config_frame,
            button_specs=[
                {
                    "text": "开始专注",
                    "command": self._on_start_clicked,
                    "widget_ref": start_button_ref,
                }
            ],
            error_var=self.error_var,
        )
        self.start_button = start_button_ref[0]

    def _build_session_view(self) -> None:
        self.session_progress = self._create_countdown_card(self.session_frame)
        self._build_status_panel(self.session_frame, self.session_hint_var)

        switch_button_ref = [None]
        end_button_ref = [None]
        self._build_action_panel(
            self.session_frame,
            button_specs=[
                {
                    "text": "切换到胶囊模式",
                    "command": self._on_switch_to_capsule_clicked,
                    "widget_ref": switch_button_ref,
                },
                {
                    "text": "结束专注",
                    "command": self._on_end_session_clicked,
                    "fg_color": "#E2E8F0",
                    "hover_color": "#CBD5E1",
                    "text_color": "#0F172A",
                    "widget_ref": end_button_ref,
                },
            ],
            height=96,
        )
        self.switch_mode_button = switch_button_ref[0]
        self.end_session_button = end_button_ref[0]

    def _bind_preview_updates(self) -> None:
        self.total_minutes_var.trace_add("write", self._on_total_minutes_changed)
        self.capsule_mode_var.trace_add("write", self._on_capsule_mode_changed)
        self._update_preview_countdown()

    def _show_view(self, view: ctk.CTkFrame) -> None:
        self.config_frame.pack_forget()
        self.session_frame.pack_forget()
        view.pack(fill="both", expand=True)

    def _on_total_minutes_changed(self, *_args) -> None:
        self._update_preview_countdown()

    def _on_capsule_mode_changed(self, *_args) -> None:
        self._emit_capsule_mode_change()

    def _emit_capsule_mode_change(self) -> None:
        if callable(self.on_start_mode_change):
            self.on_start_mode_change("capsule" if bool(self.capsule_mode_var.get()) else "main")

    def selected_start_mode(self) -> str:
        return "capsule" if bool(self.capsule_mode_var.get()) else "main"

    def _update_preview_countdown(self) -> None:
        self.countdown_var.set(format_minutes_preview(self.total_minutes_var.get()))
        self.preview_progress.set(0)

    def _on_start_clicked(self) -> None:
        try:
            config = SessionConfig(
                total_minutes=int(self.total_minutes_var.get().strip()),
                interval_min_minutes=float(self.interval_min_var.get().strip()),
                interval_max_minutes=float(self.interval_max_var.get().strip()),
                break_seconds=int(self.break_seconds_var.get().strip()),
                finish_break_minutes=int(self.finish_break_minutes_var.get().strip()),
                sound_enabled=bool(self.sound_var.get()),
                seed=None,
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
        self.finish_break_minutes_var.set(str(config.finish_break_minutes))
        self.sound_var.set(config.sound_enabled)
        self.capsule_mode_var.set(normalize_start_mode(config.start_mode) == "capsule")
        self._update_preview_countdown()

    def show_error(self, text: str) -> None:
        self.error_var.set(text)

    def show_config_view(self, status_message: str = "准备开始专注") -> None:
        self.session_hint_var.set(status_message)
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

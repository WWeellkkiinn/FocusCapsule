from __future__ import annotations

import customtkinter as ctk

from focuscapsule.state import SessionConfig


class MainSettingsWindow(ctk.CTk):
    def __init__(self, on_start) -> None:
        super().__init__()
        self.title("FocusCapsule")
        self.geometry("420x360")
        self.resizable(False, False)
        self.configure(fg_color="#FFFFFF")
        self.on_start = on_start

        self.total_minutes_var = ctk.StringVar(value="25")
        self.interval_min_var = ctk.StringVar(value="3")
        self.interval_max_var = ctk.StringVar(value="5")
        self.break_seconds_var = ctk.StringVar(value="10")
        self.sound_var = ctk.BooleanVar(value=True)
        self.seed_var = ctk.StringVar(value="")
        self.error_var = ctk.StringVar(value="")

        self._build()

    def _build(self) -> None:
        frame = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=16,
            border_width=0,
        )
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        fields = [
            ("专注总时长(分钟)", self.total_minutes_var),
            ("随机区间最小值(分钟)", self.interval_min_var),
            ("随机区间最大值(分钟)", self.interval_max_var),
            ("休息时长(秒)", self.break_seconds_var),
            ("随机种子(可选)", self.seed_var),
        ]

        for idx, (label, var) in enumerate(fields):
            ctk.CTkLabel(frame, text=label, text_color="#243447").grid(
                row=idx, column=0, sticky="w", pady=(8, 4)
            )
            ctk.CTkEntry(
                frame,
                textvariable=var,
                width=220,
                fg_color="#FFFFFF",
                border_color="#C9D4E3",
                text_color="#0F172A",
            ).grid(row=idx, column=1, sticky="ew", pady=(8, 4))

        ctk.CTkSwitch(frame, text="声音提示", variable=self.sound_var, text_color="#243447").grid(
            row=len(fields), column=0, columnspan=2, sticky="w", pady=(10, 4)
        )

        ctk.CTkButton(frame, text="开始专注", command=self._on_start_clicked).grid(
            row=len(fields) + 1, column=0, columnspan=2, sticky="ew", pady=(14, 6)
        )

        ctk.CTkLabel(frame, textvariable=self.error_var, text_color="#ff6b6b").grid(
            row=len(fields) + 2, column=0, columnspan=2, sticky="w"
        )

        frame.columnconfigure(1, weight=1)

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
            )
        except ValueError:
            self.error_var.set("请输入合法数字")
            return
        self.error_var.set("")
        self.on_start(config)

    def set_form(self, config: SessionConfig) -> None:
        self.total_minutes_var.set(str(config.total_minutes))
        self.interval_min_var.set(str(config.interval_min_minutes))
        self.interval_max_var.set(str(config.interval_max_minutes))
        self.break_seconds_var.set(str(config.break_seconds))
        self.sound_var.set(config.sound_enabled)
        self.seed_var.set("" if config.seed is None else str(config.seed))

    def show_error(self, text: str) -> None:
        self.error_var.set(text)

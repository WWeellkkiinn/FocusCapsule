# FocusCapsule

Windows 桌面随机微休息专注工具。

## 运行环境要求（必须）

- 运行与打包必须使用 **Windows 的 Anaconda Python**（建议 `C:\Users\<username>\anaconda3\envs\FocusCapsule\python.exe`）。
- 不使用 WSL 内的 Python 解释器运行本项目（包括 `~/anaconda3/bin/python`）。
- 如果缺少依赖，必须安装到 **Windows 的 `FocusCapsule` 环境**，不要安装到 WSL Python 或其他 conda 环境。
- 如在 WSL 中触发 Windows 命令，必须调用 Windows 绝对路径（如 `/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe`）。

## 打包注意

- 必须只通过 `scripts/build_win.bat` 打包，不要手动执行 `pyinstaller`。
- 打包脚本会强制使用 `C:\Users\<username>\anaconda3\envs\FocusCapsule\python.exe`，并重写构建期 `PATH`，避免误用 base 环境的 Tcl/Tk DLL。
- 历史问题的根因是：`init.tcl` 来自 `8.6.15`，但构建时错误带入了 base 环境的 `tcl86t.dll/tk86t.dll 8.6.14`，导致启动时报 `Can't find a usable init.tcl`。
- 打包前先关闭正在运行的旧版 `FocusCapsule.exe`，否则 `dist` 目录可能被系统锁定，导致清理或重打包失败。

## 常用命令

### 运行源码
```bat
cd /d C:\dev\FocusCapsule
C:\Users\<username>\anaconda3\envs\FocusCapsule\python.exe main.py
```

### 安装依赖
```bat
cd /d C:\dev\FocusCapsule
C:\Users\<username>\anaconda3\envs\FocusCapsule\python.exe -m pip install -r requirements.txt
```

### 打包
```bat
cd /d C:\dev\FocusCapsule
scripts\build_win.bat
```

### 产物
`dist/FocusCapsule/FocusCapsule.exe`

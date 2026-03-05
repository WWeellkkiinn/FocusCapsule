# FocusCapsule

Windows 桌面随机微休息专注工具。

## 运行环境要求（必须）

- 运行与打包必须使用 **Windows 的 Anaconda Python**（建议 `C:\Users\<username>\anaconda3\envs\FocusCapsule\python.exe`）。
- 不使用 WSL 内的 Python 解释器运行本项目（包括 `~/anaconda3/bin/python`）。
- 如在 WSL 中触发 Windows 命令，必须调用 Windows 绝对路径（如 `/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe`）。

## 本次大型 Bug

- **现象：** 打包后启动报错：`Can't find a usable init.tcl`，并提示 `have 8.6.14, need exactly 8.6.15`。
- **原因：** 程序启动时加载了外部 Anaconda 的 Tcl/Tk 运行时（旧版本），与应用打包内置 Tcl 脚本版本不一致。
- **修复方案：**
  - 启动最早阶段清理 `TCL_LIBRARY/TK_LIBRARY/TCLLIBPATH/PYTHONHOME/PYTHONPATH`。
  - 运行时强制绑定包内 Tcl/Tk（`scripts/pyi_rth_tkfix.py` + `focuscapsule/runtime_env.py`）。
  - 打包脚本固定环境并隔离 PATH，只使用 `FocusCapsule` 环境。
  - 改为 `PyInstaller --onedir`，降低 onefile 解包链带来的冲突风险。

## 常用命令

### 运行源码
```bat
cd /d C:\dev\FocusCapsule
C:\Users\<username>\anaconda3\envs\FocusCapsule\python.exe main.py
```

### 打包
```bat
cd /d C:\dev\FocusCapsule
scripts\build_win.bat
```

### 产物
`dist/FocusCapsule/FocusCapsule.exe`

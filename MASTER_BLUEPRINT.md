# 蓝图：修复 FocusCapsule 打包后 Tcl/Tk 版本冲突

## 1. 核心逻辑 (What)

- **业务目标：** 修复 `FocusCapsule.exe` 启动时的 `Can't find a usable init.tcl` 与 `version conflict for package "Tcl"` 异常，确保打包产物可正常启动。
- **核心规则：**
  - 打包环境中的 `python/_tkinter`、`tcl`、`tk` 必须版本一致。
  - PyInstaller 构建时必须显式使用目标 Conda 环境解释器，禁止混用其他 Python 或 PATH。
  - 打包前必须清理旧缓存（`build/`、`dist/`、旧 `.spec`），避免携带旧版 `_tcl_data`。
  - 打包后必须执行“可启动验证”，确认不再出现 Tcl 版本冲突。

## 2. 技术实现 (How)

- **数据/文件结构：**
  - `requirements.txt`：保留 Python 依赖。
  - `scripts/build_win.bat`：新增标准化 Windows 打包脚本。
  - `scripts/check_tcl.ps1`：新增 Tcl/Tk 版本自检脚本。
  - `README.md`：补充“固定环境打包流程”。
- **核心函数/模块：**
  - `scripts/check_tcl.ps1`
    - 使用指定 Python 解释器（可通过 `-PythonExe` 参数或 `python` 命令发现）输出：
      - `import tkinter; tkinter.Tcl().eval('info patchlevel')`
      - `import _tkinter; print(_tkinter.TK_VERSION, _tkinter.TCL_VERSION)`
    - 输出版本必须一致（示例：`8.6.15 / 8.6.15`）。
  - `scripts/build_win.bat`
    - 使用 `PYTHON_EXE` 环境变量指定解释器（未设置时自动查找 `python`）
    - 构建前删除：`build`、`dist`、`FocusCapsule.spec`
    - 执行：
      - `python -m pip install -r requirements.txt`
      - `python -m PyInstaller --noconfirm --onedir --windowed --runtime-hook scripts/pyi_rth_tkfix.py --name FocusCapsule main.py`
    - 期望产物路径：`dist/FocusCapsule/FocusCapsule.exe`
- **约束条件：**
  - 禁止使用 `conda run` 打包。
  - 禁止在 WSL Python 环境下执行 Windows 打包。
  - 禁止从其他 Conda 环境复用 `build/` 或 `.spec`。
  - 如 `check_tcl.ps1` 检测到 `Tcl/Tk` 不一致，必须先修复环境再打包。

## 3. 执行清单 (TODO List)

*(下游执行者必须严格按此清单执行，并在完成后标记 `[x]`)*

- [x] **Task 1:** 新增 `scripts/check_tcl.ps1`，输出 `_tkinter` 与 Tcl patchlevel，并在不一致时返回非 0。
- [x] **Task 2:** 新增 `scripts/build_win.bat`，固定解释器路径并包含清理旧构建产物步骤。
- [x] **Task 3:** 在 Windows 侧执行环境校验：
  - `conda list -n FocusCapsule tcl tk python`（如使用 Conda）
  - `powershell -File scripts/check_tcl.ps1`（或 `powershell -File scripts/check_tcl.ps1 -PythonExe <path>`）
- [x] **Task 4:** 若版本不一致，统一环境版本（推荐 `python 3.11 + tcl/tk 8.6.15`），并再次通过 `check_tcl.ps1`。
- [x] **Task 5:** 使用 `scripts/build_win.bat` 重新打包，生成 `dist/FocusCapsule/FocusCapsule.exe`。
- [x] **Task 6:** 执行可启动验证：启动 `dist/FocusCapsule.exe`，确认无 `init.tcl` 异常弹窗。
- [x] **Task 7:** 更新 `README.md` 的打包章节，明确“固定环境 + 清缓存 + 校验版本”流程。
- [x] **Task 8:** 回传证据：
  - `conda list` 关键行
  - `check_tcl.ps1` 输出
  - PyInstaller 成功日志摘要
  - 启动验证结果截图或输出

## 4. 验收规则

- `dist/FocusCapsule.exe` 在目标机器可直接启动。
- 不出现 `Failed to execute script 'main'`。
- 不出现 `Can't find a usable init.tcl`。
- 不出现 `version conflict for package "Tcl"`。
- 回传证据完整且与蓝图一致。

## 5. 假设/默认值

- 默认目标环境：通过 `PYTHON_EXE` 环境变量或 `python` 命令指定。
- 默认继续使用 `PyInstaller --onedir --windowed`。
- 默认 Windows 10/11。

## 6. 对 `$todo-executor` 的执行指令

- 严格按 `Task 1 -> Task 8` 顺序执行。
- 每项任务必须给出可复核证据后再标记 `[x]`。
- 若发现环境版本无法对齐，先回传阻塞点与替代方案，不得跳过校验直接打包。

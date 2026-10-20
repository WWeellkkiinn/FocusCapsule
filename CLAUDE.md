# CLAUDE.md

FocusCapsule 是 Windows 专属的桌面专注计时器：屏幕底部一条仿"灵动岛"深色胶囊条，支持专注倒计时、随机微休息提醒（防习惯化，创意来自 B 站 UP 主"择恩"）、完成休息与自动循环。已发布到 GitHub（WWeellkkiinn/FocusCapsule，MIT）。

## 如何验证改动

- 完整验证只能在 Windows 侧跑（依赖 Win32 API + PyQt6），WSL 里起不来 UI：
  - 日常方式：Windows 里双击 `focuscapsule.vbs`（读 `.python-path` 用 pythonw 无控制台启动）。
  - 终端方式（WSL 里可直接调 Windows Python）：
    `cd /mnt/c/dev/FocusCapsule && /mnt/c/Users/asd13/anaconda3/envs/FocusCapsule/python.exe main.py`
  - 预期结果：主屏底部居中出现深色胶囊条；悬停展开设置面板；点"开始"进度条走动；右键双击胶囊条退出。
- 纯逻辑模块（scheduler/timer/config/state）不依赖 Qt，可在 WSL 快速冒烟：
  `cd /mnt/c/dev/FocusCapsule && python3 -c "from focuscapsule.scheduler import build_trigger_points; print(build_trigger_points(1500,180,300,60,seed=1))"`
  预期输出降序触发点列表，如 `[1303, 1051, 763, 481, 204]`。
- 没有测试可跑：tests/ 已在提交 25d984d 整体删除（requirements.txt 里的 pytest 是残留，勿据此以为有测试套件）。

## 设计取舍

- 微休息触发点由 scheduler.py 从会话末尾倒推随机生成（带 guard_tail 保护尾段），随机化是刻意的——固定间隔会让大脑习惯化，提醒失效。
- 圆角胶囊外形靠 Win32 区域遮罩（win32_bar.py `set_bottom_bar_mask`）实现，而非透明窗口；`setup_toolwindow` 把窗口设为工具窗口以隐藏任务栏图标。
- 部署方式选了 VBS + `.python-path` 文件（install.py 写入当前 pythonw 路径），而不是快捷方式或打包 exe——改代码后双击即生效，无需重新打包。
- pyvda（virtual_desktop.py）的用途：切换 Windows 虚拟桌面时把胶囊条挪到当前桌面，让它"跟着人走"。
- runtime_env.py 在冻结（PyInstaller）模式下会清洗 PATH 中的 anaconda DLL 目录——否则打包后的 exe 会因 DLL 冲突崩溃；同时启用 PER_MONITOR_AWARE_V2 DPI。

## 踩过的坑

- 收起动画圆角突变为直角：Win32 遮罩更新早于 QML 渲染线程 → 采用"遮罩延迟收缩"：展开时逐帧推大遮罩，收起时遮罩不动，300ms Timer（略长于 250ms 收起动画）后一次性收缩。见 bar.qml 的 `maskShrinkTimer` 与提交 b8b8271。改动画时长时必须同步改这个 Timer 间隔。
- **CRLF 假改动**：`git status` 显示 bar.qml / bar_window.py 各 500+ 行"修改"，实为纯行尾差异（`git diff --ignore-cr-at-eol` 为空）。仓库内是 LF，Windows 编辑器会把工作区改成 CRLF，且本仓库无 .gitattributes、autocrlf 未设置。别把这种 diff 当真实改动分析，也别原样提交污染历史。
- `scripts/build_win.bat` 当前是坏的：它要求 `assets\FocusCapsule.ico`，但该文件已随 25d984d 删除，跑了会 exit 4。要打包需先恢复图标或去掉 `--icon`。日常运行不走打包，无影响。

## 隐藏依赖 / 部署链路

- 绑定本机 conda 环境 `C:\Users\asd13\anaconda3\envs\FocusCapsule`：`.python-path`（已 gitignore，机器相关）和 build_win.bat 里均硬编码此路径。换机器需重跑 `python install.py`。
- 用户配置持久化在 Windows 用户目录 `~/.focuscapsule/config.json`（config.py），删掉即恢复默认设置。
- 独立项目，与 /mnt/c/dev 下其他项目无依赖关系；远端仅 GitHub WWeellkkiinn/FocusCapsule。

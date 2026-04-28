# FocusCapsule

[English](README.md) | 中文

一个极简的 Windows 专注计时器，以细长浮岛的形式贴在屏幕底部。

## 致谢

**随机微休息提醒**这一核心创意来自 **择恩**，最早在[这个视频](https://b23.tv/Ovxmg6q)中提出，全部创意归其所有。FocusCapsule 仅是对该方法的桌面端实现。

## 功能

- **细长底部悬浮条** — 深色胶囊贴在主显示器底部边缘
- **专注倒计时** — 可配置时长，实时进度条
- **随机微休息** — 在设定的最小/最大范围内随机触发，刻意的随机性防止习惯化
- **完成休息** — 专注结束后的冷静期
- **休息动画** — 休息倒计时时进度条从中心向两端对称收缩
- **边缘吸附** — 拖到左/右边缘松手后自动居中
- **暂停 / 继续** — 随时暂停，不丢失进度
- **悬停展开** — 鼠标悬停展开设置面板；在 bar 任意位置右键双击退出
- **自动保存** — 配置在会话之间自动持久化

## 环境要求

- Windows 10 / 11
- Python 3.11+

## 安装

```bat
pip install -r requirements.txt
python install.py
```

`install.py` 将当前 `pythonw.exe` 的路径写入 `.python-path`，供 VBS 启动器无控制台启动。

## 运行

双击 `focuscapsule.vbs` 启动（无控制台窗口）。

或从终端运行：

```bat
python main.py
```

## 设置说明（悬停展开）

| 字段 | 说明 |
|---|---|
| 专注时长 | 专注总时长（分钟） |
| 完成休息 | 专注结束后的休息时长（分钟） |
| 微休息 | 每次微休息的时长（秒） |
| 休息间隔 | 微休息随机触发范围（最小 ~ 最大，分钟） |

**开始** — 启动 · **暂停** — 暂停/继续 · **结束** — 提前结束 · **重启** — 以相同配置重新开始

## 项目结构

```
focuscapsule/
  qt_app.py        # 应用核心、状态机、Tick 循环
  state.py         # 会话状态与配置数据类
  timer.py         # 单调时钟专注/休息计时器
  scheduler.py     # 随机触发点生成器
  config.py        # JSON 配置持久化（~/.focuscapsule/config.json）
  ui/
    bar.qml        # QML UI — 进度条本体
    bar_bridge.py  # Python ↔ QML 桥接（信号/槽）
    bar_window.py  # Qt 窗口管理、Win32 Mask、吸附动画
    win32_bar.py   # Win32 工具函数（DPI、区域遮罩、工具窗口）
main.py            # 入口
install.py         # 一次性配置
focuscapsule.vbs   # 静默启动器（无控制台）
```

## 许可

MIT

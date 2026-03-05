# FocusCapsule

Windows 桌面随机微休息专注工具（CustomTkinter）。

## 功能

- 主设置窗口：专注时长、随机区间、休息时长、声音开关、可选随机种子
- 悬浮胶囊窗口：仅显示总倒计时与总进度
- 全屏休息蒙版：倒计时 + `Esc` 跳过（支持多显示器覆盖）
- 单循环计时：基于单调时钟校正，降低 `after()` 漂移误差
- 配置持久化：`~/.focuscapsule/config.json`

## 目录

- `main.py`：入口
- `focuscapsule/app.py`：应用控制器
- `focuscapsule/state.py`：状态机与参数校验
- `focuscapsule/scheduler.py`：随机触发点生成
- `focuscapsule/timer.py`：高精度计时
- `focuscapsule/ui/`：三个窗口 UI
- `tests/`：核心逻辑测试

## 环境要求

- Windows 10/11
- Windows Conda（示例路径：`C:\Users\asd13\anaconda3`）

## 创建环境

```bat
C:\Users\asd13\anaconda3\Scripts\conda.exe create -y -n FocusCapsule python=3.11
```

## 安装依赖

```bat
C:\Users\asd13\anaconda3\envs\FocusCapsule\python.exe -m pip install -r C:\dev\FocusCapsule\requirements.txt
```

## 运行

```bat
cd /d C:\dev\FocusCapsule
C:\Users\asd13\anaconda3\envs\FocusCapsule\python.exe main.py
```

## 测试

```bat
cd /d C:\dev\FocusCapsule
C:\Users\asd13\anaconda3\envs\FocusCapsule\python.exe -m pytest -q
```

## 打包

```bat
cd /d C:\dev\FocusCapsule
C:\Users\asd13\anaconda3\envs\FocusCapsule\python.exe -m PyInstaller --noconfirm --onefile --windowed --name FocusCapsule main.py
```

产物：`dist/FocusCapsule.exe`

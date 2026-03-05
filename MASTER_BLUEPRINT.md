# 蓝图：FocusCapsule 随机微休息专注软件 MVP

## 1. 核心逻辑 (What)

- **业务目标：** 提供一个“不可预知打断点”的桌面专注工具，在单次专注周期内插入随机微休息，降低久坐与视觉疲劳。
- **目标用户：** 需要长时间电脑工作的个人用户（Windows 桌面）。
- **核心规则：**
  - 用户输入：专注总时长（分钟）、随机打断区间最小值/最大值（分钟）、微休息时长（秒）、声音开关。
  - 系统在“开始专注”时一次性预计算所有微休息触发节点，运行期不再重算。
  - UI 只展示“总剩余时间 + 总进度”，禁止展示“下一次微休息倒计时”。
  - 命中触发节点后进入全屏休息蒙版，休息倒计时结束自动返回专注；用户按 `Esc` 可立即跳过当前休息。
  - 仅当专注时间真实累计到 0 才结束会话并给出完成反馈。
- **状态机定义：**
  - `IDLE`：参数可编辑，未开始。
  - `FOCUSING`：专注计时进行中，更新胶囊倒计时与进度。
  - `RESTING`：全屏休息倒计时中，暂停扣减专注剩余时间。
  - `FINISHED`：本轮结束，展示完成信息并可返回 `IDLE`。
- **状态迁移规则：**
  - `IDLE -> FOCUSING`：点击“开始专注”且参数校验通过。
  - `FOCUSING -> RESTING`：当前剩余秒数命中触发节点。
  - `RESTING -> FOCUSING`：休息倒计时归零或用户按 `Esc`。
  - `FOCUSING -> FINISHED`：专注剩余秒数归零。
  - `FINISHED -> IDLE`：用户关闭完成提示并重置界面。

## 2. 技术实现 (How)

- **数据/文件结构：**
  - `main.py`：程序入口，应用生命周期管理。
  - `focuscapsule/app.py`：应用控制器，连接 UI 与状态机。
  - `focuscapsule/state.py`：状态枚举、会话数据模型、事件分发。
  - `focuscapsule/scheduler.py`：随机触发节点预计算逻辑。
  - `focuscapsule/timer.py`：高精度 Tick 驱动（基于单调时钟校正）。
  - `focuscapsule/ui/main_window.py`：设置窗口。
  - `focuscapsule/ui/capsule_window.py`：悬浮胶囊窗口。
  - `focuscapsule/ui/overlay_window.py`：全屏休息蒙版。
  - `focuscapsule/config.py`：配置读写（JSON）。
  - `requirements.txt`：依赖定义。
- **会话数据结构（建议）：**
  - `SessionConfig(total_minutes, interval_min_minutes, interval_max_minutes, break_seconds, sound_enabled)`
  - `SessionRuntime(state, focus_total_sec, focus_remaining_sec, break_remaining_sec, trigger_points_sec, started_monotonic, last_tick_monotonic)`
- **核心函数/模块：**
  - `validate_config(config) -> list[str]`
    - 规则：
      - `total_minutes >= 5`
      - `1 <= interval_min_minutes <= interval_max_minutes`
      - `break_seconds` 在 `5~120`
      - `interval_max_minutes * 60 < total_minutes * 60`
  - `build_trigger_points(total_sec, min_interval_sec, max_interval_sec, guard_tail_sec) -> list[int]`
    - 从 `total_sec` 递减采样间隔，累计得到触发点。
    - 触发点必须满足：`guard_tail_sec < point < total_sec`。
    - 去重、降序排序。
    - 默认 `guard_tail_sec = max(45, break_seconds * 2)`，确保结束前不再强插休息。
  - `tick(now_monotonic)`
    - 计算 `elapsed = floor(now_monotonic - started_monotonic) - paused_break_accumulated`。
    - `focus_remaining_sec = max(0, focus_total_sec - elapsed)`，避免 `after(1000)` 漂移累积。
    - 在 `FOCUSING` 中仅根据 `focus_remaining_sec` 判定节点命中。
  - `enter_rest(trigger_point)` / `exit_rest(reason)`
    - 进入休息时记录原因与时间戳；退出时恢复专注态并继续主循环。
  - `play_alert(enabled)`
    - 默认使用 `winsound`；若不可用则静默降级。
- **交互与边界处理：**
  - 全屏蒙版使用 `attributes('-topmost', True)` + `overrideredirect(True)`。
  - 多显示器场景：每块屏幕创建同款蒙版窗口（同一倒计时源）。
  - `Esc` 只影响当前一次休息，不影响后续随机节点。
  - 关闭主窗口或异常退出时，立即销毁全部顶层窗口并结束计时循环。
- **配置持久化：**
  - 文件：`~/.focuscapsule/config.json`。
  - 仅保存上次参数与声音开关，不保存进行中的会话状态。
- **打包规范：**
  - 使用 C 盘 Conda 环境内解释器直调 `PyInstaller`。
  - 产物目标：`dist/FocusCapsule.exe`。
- **约束条件：**
  - 仅允许单线程 UI 驱动（`CustomTkinter.after()`），禁止为计时新增工作线程。
  - 随机逻辑必须可复现调试：允许可选传入 `seed`（默认 `None`）。
  - 不引入联网依赖，不上传任何用户数据。

## 3. 验收标准

- **功能验收：**
  - 可从设置窗口启动一次完整专注流程。
  - 胶囊窗仅显示总倒计时与总进度，不出现下一次休息信息。
  - 休息蒙版可自动结束，且 `Esc` 可在 200ms 内响应并返回专注态。
  - 专注剩余时间归零后进入完成态并允许重置。
- **算法验收：**
  - 触发点全部位于 `(guard_tail_sec, total_sec)`。
  - 触发点严格降序、无重复。
  - 在固定 `seed` 下，同配置生成结果一致。
- **精度验收：**
  - 30 分钟会话累计时间误差不超过 ±2 秒。
- **稳定性验收：**
  - 连续运行 3 轮会话无崩溃、无窗口残留。

## 4. 假设/默认值

- 默认参数：`25` 分钟专注、`3~5` 分钟随机区间、`10` 秒微休息、声音开启。
- 平台范围：首版仅支持 Windows 10/11。
- 首版不提供暂停专注按钮，不提供历史统计。

## 5. 执行清单 (TODO List)

*(下游执行者必须严格按此清单执行，并在完成后标记 `[x]`)*

- [x] **Task 1:** 初始化项目结构与依赖（`CustomTkinter`、`PyInstaller`），创建 `main.py` 与 `focuscapsule/` 模块骨架。
- [x] **Task 2:** 实现 `SessionConfig` 参数校验逻辑与错误提示文案。
- [x] **Task 3:** 实现 `build_trigger_points` 随机节点生成函数（含边界保护、排序去重、可选 seed）。
- [x] **Task 4:** 实现单调时钟驱动的 `tick` 逻辑，确保长时误差控制在验收范围。
- [x] **Task 5:** 实现状态机与事件分发（`IDLE/FOCUSING/RESTING/FINISHED`）并接入主循环。
- [x] **Task 6:** 完成主设置窗口 UI（参数输入、声音开关、开始按钮、校验反馈）。
- [x] **Task 7:** 完成悬浮胶囊窗口 UI（无边框置顶、可拖动、总倒计时、进度条）。
- [x] **Task 8:** 完成全屏休息蒙版（多屏覆盖、倒计时、Esc 跳过、自动返回）。
- [x] **Task 9:** 接入声音提醒与静默降级策略（优先 `winsound`）。
- [x] **Task 10:** 实现配置持久化（`~/.focuscapsule/config.json` 读写）。
- [x] **Task 11:** 补充自动化测试与手工验收脚本（算法、状态迁移、计时精度关键路径）。
- [x] **Task 12:** 使用 Conda 环境执行打包，产出 `dist/FocusCapsule.exe` 并验证可启动。
- [x] **Task 13:** 汇总执行证据（测试结果、打包日志、验收截图）并回传给 `$product-manager` 进行一致性验收。

## 6. 对 `$todo-executor` 的执行指令

- 严格按 `Task 1 -> Task 13` 顺序执行。
- 每完成一项任务，提供对应证据（代码位置、命令、输出摘要）。
- 未提供证据的任务不得标记 `[x]`。
- 若实现与蓝图冲突，先回传冲突点与建议，不得自行偏离蓝图。

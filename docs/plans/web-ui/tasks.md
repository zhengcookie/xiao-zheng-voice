# Web UI 界面 — Tasks

> 创建时间：2025-09-14

## Issue 1: 项目骨架与 Gradio 基础框架

### Task 1.1: 创建项目配置文件

**类型**: WRITE
**依赖**: None

**范围**:
- 要触及的文件: `pyproject.toml`, `requirements.txt`
- 要遵循的模式: Python 项目标准结构

**任务描述**:
创建 `pyproject.toml` 配置项目元数据（名称、版本、Python 版本要求）。更新 `requirements.txt` 添加 Gradio、librosa、pydub 等 Web UI 所需依赖。确保 `pip install -r requirements.txt` 能成功安装。

**完成标准**:
`requirements.txt` 包含 gradio>=4.0, librosa, pydub, soundfile, scipy。安装后无报错。

---

### Task 1.2: 创建工具函数模块

**类型**: WRITE
**依赖**: Task 1.1

**范围**:
- 要触及的文件: `src/utils.py`
- 要遵循的模式: 纯函数，无副作用（除文件操作）

**任务描述**:
创建 `src/utils.py`，实现以下工具函数：
- `ensure_dir(path)` — 确保目录存在
- `get_audio_duration(file_path)` — 获取音频时长（秒）
- `format_duration(seconds)` — 格式化时长显示
- `format_size(bytes)` — 格式化文件大小显示
- `validate_audio_format(file_path)` — 校验音频格式是否支持

**完成标准**:
每个函数有 docstring，接收一个 .wav 文件路径调用 `get_audio_duration` 返回正确秒数。

---

### Task 1.3: 创建 Gradio 应用入口与 Tab 布局

**类型**: WRITE
**依赖**: Task 1.2

**范围**:
- 要触及的文件: `app.py`, `src/__init__.py`
- 要遵循的模式: Gradio Blocks API

**任务描述**:
创建 `src/__init__.py`（空文件）。创建 `app.py`，使用 Gradio Blocks 构建应用：
- 顶部标题：「🎙️ Xiao Zheng Voice — 声音克隆工具」
- 三个 Tab：「上传音频」「训练模型」「合成语音」
- 每个 Tab 内有占位文本说明该功能
- 底部状态栏显示当前工作空间路径
- 启动参数：`server_name="0.0.0.0", server_port=7860`

**完成标准**:
运行 `python app.py` 后浏览器打开 `http://localhost:7860`，三个 Tab 正确显示，切换正常。

---

### Task 1.4: 创建工作空间初始化脚本

**类型**: WRITE
**依赖**: Task 1.3

**范围**:
- 要触及的文件: `src/workspace.py`
- 要遵循的模式: 启动时自动执行

**任务描述**:
创建 `src/workspace.py`，实现 `init_workspace()` 函数：
- 在项目根目录下创建 `workspace/` 目录
- 创建子目录：`uploads/`, `processed/`, `models/`, `outputs/`
- 每个目录放一个 `.gitkeep` 文件
- 在 `app.py` 启动时调用 `init_workspace()`

**完成标准**:
运行 `python app.py` 后 `workspace/` 目录及其子目录自动创建。

---

## Issue 2: 音频上传与预处理

### Task 2.1: 创建音频上传模块

**类型**: WRITE
**依赖**: Task 1.3

**范围**:
- 要触及的文件: `src/uploader.py`
- 要遵循的模式: 纯函数处理，返回结果对象

**任务描述**:
创建 `src/uploader.py`，实现以下函数：
- `validate_upload(file_path) -> (bool, str)` — 校验文件格式和大小
- `get_audio_info(file_path) -> dict` — 返回 {name, format, duration, size}
- `save_upload(file_path, filename) -> str` — 保存到 workspace/uploads/，返回保存路径

**完成标准**:
传入 .wav 文件返回 (True, "")，传入 .txt 文件返回 (False, "仅支持 WAV/MP3/FLAC")。

---

### Task 2.2: 在上传 Tab 中集成文件上传组件

**类型**: WRITE
**依赖**: Task 2.1, Task 1.3

**范围**:
- 要触及的文件: `app.py`
- 要遵循的模式: Gradio File + Event callback

**任务描述**:
在 `app.py` 的「上传音频」Tab 中：
- 添加 Gradio `File` 组件（支持多文件，接受 .wav/.mp3/.flac）
- 添加 `Dataframe` 组件显示已上传文件列表（文件名、时长、大小）
- 绑定上传事件：调用 `uploader.validate_upload` 和 `uploader.save_upload`
- 格式错误时用 `gr.Warning` 显示警告
- 时长 < 3 秒时用 `gr.Warning` 显示提示
- 上传成功后刷新文件列表

**完成标准**:
拖拽 .wav 文件到上传区，下方表格出现一行记录。上传 .txt 文件，页面顶部出现红色错误提示。

---

### Task 2.3: 添加音频波形预览

**类型**: WRITE
**依赖**: Task 2.2

**范围**:
- 要触及的文件: `app.py`
- 要遵循的模式: Gradio Audio 组件

**任务描述**:
在文件列表下方添加音频播放器组件：
- 用户选择文件列表中的某一行时，播放器加载对应音频
- 使用 Gradio `Audio` 组件（type="filepath", interactive=False）
- 选择事件绑定到文件列表的 `select` 事件

**完成标准**:
上传音频后，点击列表中的文件名，下方播放器加载并可播放该音频。

---

## Issue 3: 模型训练与进度监控

### Task 3.1: 创建训练封装模块

**类型**: WRITE
**依赖**: Task 1.2

**范围**:
- 要触及的文件: `src/trainer.py`
- 要遵循的模式: subprocess 隔离，threading 异步读取日志

**任务描述**:
创建 `src/trainer.py`，实现：
- `start_training(audio_dir, model_name) -> TrainingHandle` — 启动训练子进程
- `get_status(handle) -> dict` — 返回 {progress: float, logs: list[str], status: str}
- `cancel_training(handle) -> bool` — 终止子进程
- `list_models() -> list[dict]` — 列出 workspace/models/ 下的模型

注意：当前阶段用模拟训练（sleep + 随机日志输出）替代真实 GPT-SoVITS 调用，预留接口。

**完成标准**:
调用 `start_training` 返回 handle，`get_status` 返回进度 0-100 和日志列表。`cancel_training` 终止进程。

---

### Task 3.2: 在训练 Tab 中集成训练界面

**类型**: WRITE
**依赖**: Task 3.1, Task 1.3

**范围**:
- 要触及的文件: `app.py`
- 要遵循的模式: Gradio Progress + Textbox

**任务描述**:
在「训练模型」Tab 中：
- 顶部显示状态提示（有音频可训练 / 无音频请先上传）
- 模型名称输入框（默认 "my_voice"）
- 「开始训练」按钮 + 「取消训练」按钮
- `gr.Progress` 组件显示训练进度
- `gr.Textbox` 组件（interactive=False）显示滚动日志
- 训练完成显示「✅ 训练完成」状态
- 使用 `gr.Timer` 或轮询机制每 2 秒刷新状态

**完成标准**:
点击训练后进度条增长，日志每 2 秒更新，完成后状态变绿。

---

### Task 3.3: 添加 GPU 显存预检

**类型**: WRITE
**依赖**: Task 3.2

**范围**:
- 要触及的文件: `src/trainer.py`
- 要遵循的模式: torch.cuda 检查

**任务描述**:
在 `start_training` 中添加显存检查：
- 调用 `torch.cuda.mem_get_info()` 获取可用显存
- 可用显存 < 2GB 时拒绝启动，返回错误信息
- 在训练日志中输出显存信息

**完成标准**:
GPU 显存不足时点击训练显示红色错误提示，不启动训练进程。

---

## Issue 4: 语音合成与播放下载

### Task 4.1: 创建合成封装模块

**类型**: WRITE
**依赖**: Task 3.1

**范围**:
- 要触及的文件: `src/synthesizer.py`
- 要遵循的模式: 与 trainer.py 类似的模拟实现

**任务描述**:
创建 `src/synthesizer.py`，实现：
- `generate(text, model_name) -> str` — 调用模型合成音频，返回输出路径
- 当前阶段用 TTS 库（如 pyttsx3 或 edge-tts）生成示例音频，预留 GPT-SoVITS 接口

**完成标准**:
传入文本和模型名，返回一个可播放的 .wav 文件路径。

---

### Task 4.2: 在合成 Tab 中集成合成界面

**类型**: WRITE
**依赖**: Task 4.1, Task 1.3

**范围**:
- 要触及的文件: `app.py`
- 要遵循的模式: Gradio Textbox + Dropdown + Audio

**任务描述**:
在「合成语音」Tab 中：
- 模型选择下拉框（从 `trainer.list_models()` 获取选项）
- 文本输入框（placeholder="输入要合成的文本..."）
- 字数统计显示
- 「合成」按钮
- 合成完成后显示 `gr.Audio` 播放器（自动播放）
- 「下载」按钮（使用 `gr.File` 组件）
- 无模型时显示提示信息

**完成标准**:
选择模型、输入文字、点击合成，播放器出现并可播放。超过 500 字显示黄色警告。

---

### Task 4.3: 添加合成参数调整

**类型**: WRITE
**依赖**: Task 4.2

**范围**:
- 要触及的文件: `app.py`, `src/synthesizer.py`
- 要遵循的模式: Gradio Slider

**任务描述**:
在合成区域添加参数调整：
- 语速滑块（0.5x - 2.0x，默认 1.0x）
- 音高滑块（-12 - +12 半音，默认 0）
- 将参数传递给 `synthesizer.generate()`

**完成标准**:
调整语速滑块后合成的音频播放速度明显变化。

---

## Issue 5: 模型管理（查看/删除）

### Task 5.1: 扩展模型管理功能

**类型**: WRITE
**依赖**: Task 3.1

**范围**:
- 要触及的文件: `src/trainer.py`
- 要遵循的模式: 文件系统操作

**任务描述**:
在 `src/trainer.py` 中添加：
- `rename_model(old_name, new_name) -> bool` — 重命名模型目录
- `delete_model(model_name) -> bool` — 删除模型目录及文件
- `get_model_info(model_name) -> dict` — 返回模型详细信息

**完成标准**:
`rename_model("a", "b")` 后目录名变为 "b"。`delete_model("b")` 后目录消失。

---

### Task 5.2: 在合成 Tab 中添加模型管理面板

**类型**: WRITE
**依赖**: Task 5.1, Task 4.2

**范围**:
- 要触及的文件: `app.py`
- 要遵循的模式: Gradio Accordion + Button

**任务描述**:
在「合成」Tab 的模型选择区域旁添加折叠面板「模型管理」：
- 展开后显示模型列表（名称、训练时间、大小）
- 每个模型旁有「重命名」和「删除」按钮
- 重命名：弹出输入框，输入新名称后保存
- 删除：弹出确认对话框，确认后删除并刷新列表
- 删除后自动更新合成 Tab 的模型下拉框

**完成标准**:
展开模型管理面板，看到训练过的模型。点击删除，确认后模型从列表和下拉框中消失。

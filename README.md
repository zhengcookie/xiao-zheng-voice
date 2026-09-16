# Xiao Zheng Voice 🎙️

> 基于开源语音克隆技术，克隆身边人的声音。**非商业用途。**

## 📖 项目简介

本项目利用当前 GitHub 上主流的开源语音克隆（Voice Cloning）技术，实现对身边人声音的复刻与合成。所有代码和模型均来自开源社区，本项目仅用于学习和个人使用，**不作任何商业用途**。

## ✨ 功能特性

- 🎤 **声音克隆** — 仅需少量音频样本即可复刻目标声音
- 🔊 **语音合成 (TTS)** — 使用克隆的声音合成任意文本
- 🎵 **跨语言支持** — 支持中英文等多语言语音合成
- 🛠️ **易于使用** — 提供简洁的使用流程和脚本

## 🧰 参考项目

本项目基于以下优秀的开源语音克隆项目：

| 项目 | 说明 | 链接 |
|------|------|------|
| **GPT-SoVITS** | 少样本声音克隆 + TTS | [GitHub](https://github.com/RVC-Boss/GPT-SoVITS) |
| **Coqui TTS** | 开源 TTS 工具箱，支持 VITS/XTTS | [GitHub](https://github.com/coqui-ai/TTS) |
| **RVC (Retrieval-based Voice Conversion)** | 变声器，基于检索的语音转换 | [GitHub](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI) |
| **Fish Speech** | 零样本多语言语音合成 | [GitHub](https://github.com/fishaudio/fish-speech) |
| **CosyVoice** | 阿里通义实验室，可控大模型语音合成 | [GitHub](https://github.com/FunAudioLLM/CosyVoice) |
| **OpenVoice** | 精细控制语音风格的零样本 TTS | [GitHub](https://github.com/myshell-ai/OpenVoice) |

## 📁 项目结构

```
xiao-zheng-voice/
├── app.py                 # Gradio Web UI 入口
├── src/                   # 核心模块
│   ├── utils.py           # 音频与文件工具函数
│   └── workspace.py       # 工作空间目录管理
├── scripts/
│   └── smoke_test.py      # 骨架冒烟测试
├── docs/                  # 规划与调研文档
│   ├── agents/            # 技能配置（issue tracker / domain docs）
│   └── plans/web-ui/      # Web UI 规划（计划 / PRD / issues / tasks）
├── configs/               # 模型配置
├── examples/              # 示例音频
├── workspace/             # 运行期数据（自动创建，不入库）
│   ├── uploads/           # 上传的原始音频
│   ├── processed/         # 预处理后的音频
│   ├── models/            # 训练好的模型
│   └── outputs/           # 合成的音频
├── pyproject.toml         # 项目元数据与依赖
└── requirements.txt       # 锁定的依赖版本
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- **无需 GPU** — 骨架与模拟模式在 CPU 上即可运行
- GPU（≥8GB 显存）仅在接入真实 GPT-SoVITS 后端时需要

### 安装

```bash
git clone https://github.com/zhengcookie/xiao-zheng-voice.git
cd xiao-zheng-voice

# 推荐：使用虚拟环境
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 启动 Web UI

```bash
python app.py
```

然后在浏览器打开 <http://localhost:7860>。

### 验证安装

```bash
python scripts/smoke_test.py
```

该脚本会检查工作空间目录、工具函数与应用构建，无需浏览器。

### 使用流程

1. **上传音频** — 在「上传音频」Tab 上传目标人物的清晰语音（建议 3–10 分钟）
2. **训练模型** — 在「训练模型」Tab 一键训练，实时查看进度与日志
3. **合成语音** — 在「合成语音」Tab 输入文本，生成并下载语音

> ⏳ Web UI 目前为**骨架版本**（三个 Tab 与工作空间已就绪），
> 具体功能正按 `docs/plans/web-ui/` 中的计划逐步实现。

## ⚠️ 免责声明

- 本项目仅供**学习和研究**使用，**严禁**用于任何商业目的
- 使用本项目时，请遵守当地法律法规
- 请勿将本技术用于欺骗、误导或任何违法活动
- 使用前请获得被克隆声音所有者的**知情同意**

## 📄 License

[MIT License](LICENSE)

---

*Made with ❤️ for learning and exploration*

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
├── README.md          # 项目说明
├── requirements.txt   # Python 依赖
├── scripts/           # 工具脚本
├── configs/           # 模型配置文件
└── examples/          # 示例音频与输出
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- CUDA 11.8+ (推荐)
- GPU 显存 ≥ 8GB

### 安装

```bash
git clone https://github.com/zhengcookie/xiao-zheng-voice.git
cd xiao-zheng-voice
pip install -r requirements.txt
```

### 使用流程

1. **准备音频数据** — 录制目标人物的清晰语音（建议 3-10 分钟）
2. **训练模型** — 使用 GPT-SoVITS / RVC 等工具进行声音克隆
3. **合成语音** — 输入文本，生成克隆声音的语音

详细步骤请参阅各参考项目的官方文档。

## ⚠️ 免责声明

- 本项目仅供**学习和研究**使用，**严禁**用于任何商业目的
- 使用本项目时，请遵守当地法律法规
- 请勿将本技术用于欺骗、误导或任何违法活动
- 使用前请获得被克隆声音所有者的**知情同意**

## 📄 License

[MIT License](LICENSE)

---

*Made with ❤️ for learning and exploration*

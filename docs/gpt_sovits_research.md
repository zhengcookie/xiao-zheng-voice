# GPT-SoVITS API Interface Research

## 1. Architecture Overview

GPT-SoVITS is a two-stage TTS system:
- **Stage 1 (GPT/T2S)**: Text → Semantic tokens (Text2SemanticLightningModule)
- **Stage 2 (SoVITS/VITS)**: Semantic tokens → Audio waveform (SynthesizerTrn / SynthesizerTrnV3)

### Supported Versions
| Version | Output SR | Key Feature | VITS Model |
|---------|-----------|-------------|------------|
| v1 | 32kHz | Original | SynthesizerTrn |
| v2 | 32kHz | Better base, 5khr pretrained | SynthesizerTrn |
| v3 | 24kHz | Higher timbre similarity | SynthesizerTrnV3 + BigVGAN |
| v4 | 48kHz | Fixes v3 artifacts | SynthesizerTrnV3 + HiFi-GAN |
| v2Pro | 32kHz | Best quality/cost ratio | SynthesizerTrn + SV |
| v2ProPlus | 32kHz | Top v2 quality | SynthesizerTrn + SV |

---

## 2. Inference API

### 2A. Python API (TTS Class)

```python
from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config

# Initialize
config = TTS_Config("GPT_SoVITS/configs/tts_infer.yaml")
tts = TTS(config)

# Set reference audio (3-10 seconds of target voice)
tts.set_ref_audio(ref_audio_path)

# Run inference
for sr, audio_chunk in tts.run({
    "text": "要合成的文本",
    "text_lang": "zh",               # zh, en, ja, yue, ko, auto, auto_yue
    "ref_audio_path": "ref.wav",     # reference audio (3-10s)
    "prompt_text": "参考音频的文本",   # transcript of ref audio (optional but recommended)
    "prompt_lang": "zh",
    "top_k": 15,
    "top_p": 1,
    "temperature": 1,
    "text_split_method": "cut5",     # cut1-cut5 or "不切"
    "batch_size": 1,
    "batch_threshold": 0.75,
    "split_bucket": True,
    "speed_factor": 1.0,
    "fragment_interval": 0.3,
    "seed": -1,                      # -1 = random
    "parallel_infer": True,
    "repetition_penalty": 1.35,
    "sample_steps": 32,              # V3/V4 only
    "super_sampling": False,         # V3 only
    "streaming_mode": False,
    "overlap_length": 2,
    "min_chunk_length": 16,
}):
    # sr: int (sample rate, e.g. 32000)
    # audio_chunk: np.ndarray (int16 PCM)
    pass
```

**Key TTS.run() parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | str | **required** | Text to synthesize |
| `text_lang` | str | **required** | Language: zh/en/ja/yue/ko/auto/auto_yue/all_zh/all_ja/all_yue/all_ko |
| `ref_audio_path` | str | **required** | Path to 3-10s reference audio file |
| `prompt_text` | str | "" | Transcript of reference audio (improves similarity) |
| `prompt_lang` | str | **required** | Language of prompt text |
| `top_k` | int | 15 | Top-k sampling |
| `top_p` | float | 1.0 | Top-p (nucleus) sampling |
| `temperature` | float | 1.0 | Sampling temperature |
| `speed_factor` | float | 1.0 | Playback speed (0.6-1.65) |
| `seed` | int | -1 | Random seed (-1=random) |
| `sample_steps` | int | 32 | VITS sampling steps (V3/V4 only) |
| `streaming_mode` | bool/int | False | Streaming output |

**Yields:** `(sample_rate: int, audio_data: np.ndarray)` tuples

### 2B. HTTP API (FastAPI)

**Server launch:**
```bash
python api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml
```

**Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tts` | GET/POST | Synthesize speech |
| `/set_gpt_weights` | GET | Switch GPT model at runtime |
| `/set_sovits_weights` | GET | Switch SoVITS model at runtime |
| `/set_refer_audio` | GET | Set default reference audio |
| `/control` | GET | restart/exit |

**POST /tts Request Body:**
```json
{
    "text": "要合成的文本",
    "text_lang": "zh",
    "ref_audio_path": "path/to/ref.wav",
    "prompt_text": "参考音频的文本",
    "prompt_lang": "zh",
    "top_k": 15,
    "top_p": 1.0,
    "temperature": 1.0,
    "text_split_method": "cut5",
    "batch_size": 1,
    "speed_factor": 1.0,
    "seed": -1,
    "media_type": "wav",           // wav, ogg, aac, raw
    "streaming_mode": false,
    "parallel_infer": true,
    "repetition_penalty": 1.35,
    "sample_steps": 32,
    "super_sampling": false
}
```

**Response:** Raw audio bytes (HTTP 200) or JSON error (HTTP 400)

---

## 3. Training API

Training is invoked through the **Gradio WebUI** (port 9874) via a 5-stage pipeline:

### Training Pipeline Stages
1. **UVR5 Separation** (optional) — strip background music (port 9873)
2. **Slice** — chop recordings into training clips
3. **Denoise** (optional) — audio cleanup
4. **ASR** — auto-transcribe (Faster-Whisper for English, FunASR for Chinese)
5. **Proofread** — manual transcript correction (port 9871)
6. **Fine-tune** — train both SoVITS and GPT models

### Minimum Requirements
- **1 minute** of clean speech (documented minimum)
- **3-10 minutes** practical sweet spot

### Training Parameters (from WebUI)
The training is configured through the Gradio UI. Key parameters:
- **SoVITS training**: epochs, learning rate, batch size, LoRA rank
- **GPT training**: epochs, learning rate, batch size
- **Data preprocessing**: sample rate, duration limits

### GPU Requirements for Training

| Model | Min VRAM | Recommended | With LoRA | With Grad Checkpoint |
|-------|----------|-------------|-----------|---------------------|
| v2 | 4GB | 8GB+ | 4GB | — |
| v3 | 8GB | 12GB+ | 8GB | 12GB |
| v4 | 4GB | 8GB+ | — | — |
| v2Pro | 4GB | 8GB+ | — | — |

### GPU Requirements for Inference

| Model | Min VRAM | Recommended | Notes |
|-------|----------|-------------|-------|
| v1/v2 | 4GB | 6GB+ | FP16 recommended |
| v3 | 4GB | 6GB+ | + BigVGAN vocoder |
| v4 | 4GB | 6GB+ | + HiFi-GAN vocoder |
| v2Pro | 4GB | 6GB+ | + SV model |

RTX 4060 Ti (16GB): generates 1 hour of audio in ~2 minutes

---

## 4. Model File Format

### Produced Files After Training

| File Type | Extension | Content | Example |
|-----------|-----------|---------|---------|
| GPT/T2S weights | `.ckpt` | PyTorch Lightning checkpoint | `s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt` |
| SoVITS weights | `.pth` | PyTorch state dict + config | `s2G2333k.pth` |
| LoRA weights | `.pth` | LoRA adapter weights | For v3/v4 fine-tuned models |

### Pretrained Model Files
```
GPT_SoVITS/pretrained_models/
├── chinese-hubert-base/          # CNHubert SSL model
├── chinese-roberta-wwm-ext-large/ # BERT model for Chinese
├── gsv-v2final-pretrained/
│   ├── s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt  # GPT v2
│   └── s2G2333k.pth                                    # SoVITS v2
├── s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt      # GPT v1
├── s2G488k.pth                                           # SoVITS v1
├── s1v3.ckpt                                             # GPT v3/v4
├── s2Gv3.pth                                             # SoVITS v3
├── gsv-v4-pretrained/
│   ├── s2Gv4.pth                                         # SoVITS v4
│   └── vocoder.pth                                       # HiFi-GAN vocoder
├── v2Pro/
│   ├── s2Gv2Pro.pth
│   └── s2Gv2ProPlus.pth
└── models--nvidia--bigvgan_v2_24khz_100band_256x/        # BigVGAN for v3
```

### Internal Format
- **`.ckpt` files**: PyTorch Lightning checkpoints containing:
  - `weight`: model state dict
  - `config`: training config dict (includes `data.max_sec`)
  
- **`.pth` files**: Custom format via `load_sovits_new()` containing:
  - `weight`: model state dict
  - `config`: hyperparameters dict (data, model, train sections)
  - `lora_rank`: (optional) LoRA rank for fine-tuned models

### Config File (`tts_infer.yaml`)
```yaml
custom:
  bert_base_path: GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large
  cnhuhbert_base_path: GPT_SoVITS/pretrained_models/chinese-hubert-base
  device: cuda
  is_half: true
  t2s_weights_path: GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt
  vits_weights_path: GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth
  version: v2
```

---

## 5. Chinese Text Processing

### Special Requirements
1. **G2PW Model** (Chinese v2+): For polyphone disambiguation, download G2PW models and place in `GPT_SoVITS/text/G2PWModel/`
2. **BERT Model**: Uses `chinese-roberta-wwm-ext-large` for Chinese text features (1024-dim)
3. **Text Segmentation**: Uses `LangSegmenter` for automatic language detection

### Language Codes
| Code | Description |
|------|-------------|
| `zh` | Chinese-English mixed recognition |
| `all_zh` | All Chinese recognition |
| `en` | English |
| `ja` | Japanese-English mixed |
| `all_ja` | All Japanese |
| `yue` | Cantonese-English mixed |
| `all_yue` | All Cantonese |
| `ko` | Korean-English mixed |
| `all_ko` | All Korean |
| `auto` | Multi-language auto-detect |
| `auto_yue` | Multi-language with Cantonese |

### Text Preprocessing Pipeline
1. Text cleaning (`text.cleaner.clean_text`)
2. Phoneme conversion (`cleaned_text_to_sequence`)
3. BERT feature extraction (`get_bert_feature`) — only for Chinese text
4. Text splitting for long sentences (`text_segmentation_method`)

---

## 6. Integration Points

### Option A: HTTP API Wrapper (Recommended)
Run GPT-SoVITS as a separate process and call via HTTP.

```python
import httpx
import numpy as np

class GPTSoVITSClient:
    def __init__(self, base_url: str = "http://127.0.0.1:9880"):
        self.base_url = base_url
    
    async def synthesize(
        self,
        text: str,
        text_lang: str,
        ref_audio_path: str,
        prompt_text: str = "",
        prompt_lang: str = "zh",
        **kwargs
    ) -> tuple[int, np.ndarray]:
        """Returns (sample_rate, audio_data)"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/tts",
                json={
                    "text": text,
                    "text_lang": text_lang,
                    "ref_audio_path": ref_audio_path,
                    "prompt_text": prompt_text,
                    "prompt_lang": prompt_lang,
                    **kwargs
                }
            )
            # Parse WAV response
            import io, soundfile as sf
            audio, sr = sf.read(io.BytesIO(response.content))
            return sr, audio
    
    async def switch_gpt_model(self, weights_path: str):
        async with httpx.AsyncClient() as client:
            await client.get(
                f"{self.base_url}/set_gpt_weights",
                params={"weights_path": weights_path}
            )
    
    async def switch_sovits_model(self, weights_path: str):
        async with httpx.AsyncClient() as client:
            await client.get(
                f"{self.base_url}/set_sovits_weights",
                params={"weights_path": weights_path}
            )
```

### Option B: Direct Python Import
Import the TTS class directly (requires same Python environment).

```python
from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config

class GPTSoVITSDirect:
    def __init__(self, config_path: str = "GPT_SoVITS/configs/tts_infer.yaml"):
        self.config = TTS_Config(config_path)
        self.tts = TTS(self.config)
    
    def synthesize(
        self,
        text: str,
        text_lang: str,
        ref_audio_path: str,
        prompt_text: str = "",
        prompt_lang: str = "zh",
        **kwargs
    ) -> tuple[int, np.ndarray]:
        self.tts.set_ref_audio(ref_audio_path)
        for sr, chunk in self.tts.run({
            "text": text,
            "text_lang": text_lang,
            "ref_audio_path": ref_audio_path,
            "prompt_text": prompt_text,
            "prompt_lang": prompt_lang,
            **kwargs
        }):
            return sr, chunk  # Non-streaming: return first chunk
```

---

## 7. Recommended Abstraction Layer

### Base Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import numpy as np

@dataclass
class TTSRequest:
    text: str
    text_lang: str
    ref_audio_path: str
    prompt_text: str = ""
    prompt_lang: str = "zh"
    top_k: int = 15
    top_p: float = 1.0
    temperature: float = 1.0
    speed_factor: float = 1.0
    seed: int = -1
    sample_steps: int = 32  # V3/V4 only

@dataclass
class TTSResult:
    sample_rate: int
    audio_data: np.ndarray  # int16 PCM
    duration_seconds: float
    model_version: str

class BaseVoiceCloner(ABC):
    @abstractmethod
    def load_model(
        self,
        gpt_weights_path: str,
        sovits_weights_path: str,
        device: str = "auto"
    ) -> None:
        """Load model weights."""
        pass
    
    @abstractmethod
    def synthesize(self, request: TTSRequest) -> TTSResult:
        """Generate speech from text."""
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> list[str]:
        """Return list of supported language codes."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> dict:
        """Return model metadata."""
        pass
```

### Simulated Mode (for development)

```python
class SimulatedVoiceCloner(BaseVoiceCloner):
    """Mock implementation for development/testing."""
    
    def __init__(self):
        self.model_loaded = False
        self.gpt_path = None
        self.sovits_path = None
    
    def load_model(self, gpt_weights_path, sovits_weights_path, device="auto"):
        self.gpt_path = gpt_weights_path
        self.sovits_path = sovits_weights_path
        self.model_loaded = True
        print(f"[SIM] Loaded models: {gpt_weights_path}, {sovits_weights_path}")
    
    def synthesize(self, request: TTSRequest) -> TTSResult:
        """Generate silence as placeholder."""
        # Simulate processing time
        import time
        time.sleep(0.1)
        
        # Generate 1 second of silence
        sample_rate = 32000
        duration = len(request.text) * 0.1  # Rough estimate
        audio = np.zeros(int(sample_rate * duration), dtype=np.int16)
        
        return TTSResult(
            sample_rate=sample_rate,
            audio_data=audio,
            duration_seconds=duration,
            model_version="simulated"
        )
    
    def get_supported_languages(self):
        return ["zh", "en", "ja", "yue", "ko"]
    
    def get_model_info(self):
        return {
            "type": "simulated",
            "gpt_path": self.gpt_path,
            "sovits_path": self.sovits_path,
        }
```

### Real GPT-SoVITS Integration

```python
class GPTSoVITSClone(BaseVoiceCloner):
    """Real GPT-SoVITS integration via HTTP API."""
    
    def __init__(self, api_url: str = "http://127.0.0.1:9880"):
        self.api_url = api_url
        self.client = None
    
    def _ensure_client(self):
        if self.client is None:
            import httpx
            self.client = httpx.AsyncClient(timeout=60.0)
    
    def load_model(self, gpt_weights_path, sovits_weights_path, device="auto"):
        """Switch models via API endpoints."""
        import httpx
        with httpx.Client() as client:
            client.get(f"{self.api_url}/set_gpt_weights", params={"weights_path": gpt_weights_path})
            client.get(f"{self.api_url}/set_sovits_weights", params={"weights_path": sovits_weights_path})
    
    async def synthesize(self, request: TTSRequest) -> TTSResult:
        """Call GPT-SoVITS API."""
        self._ensure_client()
        
        response = await self.client.post(f"{self.api_url}/tts", json={
            "text": request.text,
            "text_lang": request.text_lang,
            "ref_audio_path": request.ref_audio_path,
            "prompt_text": request.prompt_text,
            "prompt_lang": request.prompt_lang,
            "top_k": request.top_k,
            "top_p": request.top_p,
            "temperature": request.temperature,
            "speed_factor": request.speed_factor,
            "seed": request.seed,
            "sample_steps": request.sample_steps,
        })
        
        import io, soundfile as sf
        audio, sr = sf.read(io.BytesIO(response.content))
        duration = len(audio) / sr
        
        return TTSResult(
            sample_rate=sr,
            audio_data=(audio * 32767).astype(np.int16),
            duration_seconds=duration,
            model_version="gpt-sovits"
        )
    
    def get_supported_languages(self):
        return ["zh", "en", "ja", "yue", "ko", "auto", "auto_yue"]
    
    def get_model_info(self):
        return {"type": "gpt-sovits", "api_url": self.api_url}
```

### Factory Pattern

```python
from enum import Enum

class VoiceClonerType(Enum):
    SIMULATED = "simulated"
    GPT_SOVITS = "gpt-sovits"

def create_voice_cloner(
    cloner_type: VoiceClonerType = VoiceClonerType.SIMULATED,
    api_url: str = "http://127.0.0.1:9880",
    **kwargs
) -> BaseVoiceCloner:
    if cloner_type == VoiceClonerType.SIMULATED:
        return SimulatedVoiceCloner()
    elif cloner_type == VoiceClonerType.GPT_SOVITS:
        return GPTSoVITSClone(api_url=api_url)
    else:
        raise ValueError(f"Unknown cloner type: {cloner_type}")
```

---

## 8. What to Mock in Simulated Mode

### Core Mocks
1. **Audio generation**: Return silence or pre-recorded placeholder audio
2. **Model loading**: Log and set flags, no actual GPU usage
3. **Language support**: Return the same language list as real implementation

### What NOT to Mock
1. **API interface**: Keep the same method signatures
2. **Data structures**: Use real `TTSRequest`/`TTSResult` types
3. **Error handling**: Raise same exceptions as real implementation
4. **Configuration**: Accept same config format

### Optional Advanced Mocks
- **Latency simulation**: Add artificial delays matching real inference times
- **Audio quality levels**: Return different quality placeholder audio
- **Model version detection**: Return version info based on weights path

---

## 9. Key Dependencies

```txt
# Core
torch>=2.2.2
torchaudio
numpy
soundfile
librosa

# Models
transformers          # BERT
peft                  # LoRA
pytorch_lightning     # GPT training

# API
fastapi
uvicorn
httpx                 # Client calls

# Audio processing
ffmpeg-python
```

---

## 10. Summary Table

| Aspect | Details |
|--------|---------|
| **Architecture** | Two-stage: GPT (text→semantic) + SoVITS (semantic→audio) |
| **Inference API** | Python class (`TTS`) or HTTP REST API (`/tts`) |
| **Training** | WebUI 5-stage pipeline, 1min+ audio needed |
| **Model Files** | `.ckpt` (GPT) + `.pth` (SoVITS) |
| **Min VRAM (Inference)** | 4GB |
| **Min VRAM (Training)** | 4-8GB depending on version |
| **Chinese Support** | Native, with BERT features and G2PW polyphone |
| **Languages** | zh, en, ja, yue, ko + mixed modes |
| **Integration** | HTTP API recommended for cross-process |

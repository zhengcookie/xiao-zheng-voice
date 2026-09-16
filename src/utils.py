"""音频与文件相关的通用工具函数。

这些函数保持无状态、无副作用（除显式的文件操作外），
方便在 uploader / trainer / synthesizer 等模块间复用与单测。
"""

from __future__ import annotations

import os
from pathlib import Path

# --- 常量 ---

#: 支持的音频扩展名（小写，含前导点）
SUPPORTED_AUDIO_FORMATS: frozenset[str] = frozenset({".wav", ".mp3", ".flac"})

#: 单文件大小上限：500 MB
MAX_UPLOAD_BYTES: int = 500 * 1024 * 1024

#: 低于该时长给出警告：3 秒
MIN_AUDIO_SECONDS: float = 3.0

#: 推荐的最短时长（用于提示文案）：10 秒
RECOMMENDED_AUDIO_SECONDS: float = 10.0


def ensure_dir(path: str | os.PathLike[str]) -> Path:
    """确保目录存在（含父目录），返回其 :class:`~pathlib.Path`。"""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_audio_duration(file_path: str | os.PathLike[str]) -> float:
    """返回音频时长（秒）。

    优先使用 ``soundfile``；失败时对 ``.wav`` 回退到标准库 ``wave``；
    仍无法判断时返回 ``0.0``，绝不抛异常——调用方据此决定是否告警。
    """
    path = Path(file_path)
    if not path.is_file():
        return 0.0

    try:
        import soundfile as sf

        info = sf.info(str(path))
        if info.samplerate:
            return float(info.frames) / float(info.samplerate)
    except Exception:
        pass

    if path.suffix.lower() == ".wav":
        try:
            import wave

            with wave.open(str(path), "rb") as wf:
                rate = wf.getframerate()
                if rate:
                    return wf.getnframes() / float(rate)
        except Exception:
            pass

    return 0.0


def get_file_size(file_path: str | os.PathLike[str]) -> int:
    """返回文件字节数；文件不存在时返回 ``0``。"""
    path = Path(file_path)
    try:
        return path.stat().st_size
    except OSError:
        return 0


def format_duration(seconds: float) -> str:
    """把秒数格式化为 ``m:ss`` 或 ``h:mm:ss``。"""
    total = int(round(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_size(num_bytes: int) -> str:
    """把字节数格式化为人类可读的字符串（B / KB / MB / GB）。"""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024.0 or unit == "TB":
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def validate_audio_format(file_path: str | os.PathLike[str]) -> tuple[bool, str]:
    """校验扩展名是否为受支持的音频格式。

    Returns:
        ``(ok, message)``；``ok`` 为 ``False`` 时 ``message`` 是给用户看的提示。
    """
    suffix = Path(file_path).suffix.lower()
    if not suffix:
        return False, "无法识别文件格式（缺少扩展名）"
    if suffix not in SUPPORTED_AUDIO_FORMATS:
        supported = " / ".join(sorted(f.lstrip(".").upper() for f in SUPPORTED_AUDIO_FORMATS))
        return False, f"仅支持 {supported} 格式，收到 {suffix.lstrip('.').upper()}"
    return True, ""


def validate_upload(file_path: str | os.PathLike[str]) -> tuple[bool, str]:
    """上传前的完整校验：格式 + 大小。

    Returns:
        ``(ok, message)``；``ok`` 为 ``False`` 时 ``message`` 说明拒绝原因。
    """
    path = Path(file_path)
    if not path.is_file():
        return False, f"文件不存在：{path.name}"

    ok, message = validate_audio_format(path)
    if not ok:
        return False, message

    size = get_file_size(path)
    if size <= 0:
        return False, f"文件为空：{path.name}"
    if size > MAX_UPLOAD_BYTES:
        return False, f"文件过大（{format_size(size)}），上限 {format_size(MAX_UPLOAD_BYTES)}"

    return True, ""


def collect_audio_files(directory: str | os.PathLike[str]) -> list[Path]:
    """递归收集目录下所有受支持的音频文件，按名称排序。"""
    root = Path(directory)
    if not root.is_dir():
        return []
    files = [
        p
        for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_AUDIO_FORMATS
    ]
    return sorted(files)

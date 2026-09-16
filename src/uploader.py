"""音频上传与预处理逻辑（票据 #6）。

职责：
- 把 Gradio 上传到临时目录的音频文件持久化到 ``workspace/uploads/``
- 提取元数据（时长 / 大小 / 格式）供 UI 展示
- 格式 / 大小 / 时长校验，返回用户可读的状态信息
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .utils import (
    SUPPORTED_AUDIO_FORMATS,
    get_audio_duration,
    get_file_size,
    format_duration,
    format_size,
    validate_upload,
)
from .workspace import UPLOADS_DIR

#: UI 表格的列头
TABLE_HEADERS: list[str] = ["文件名", "时长", "大小", "格式", "状态"]

#: 时长告警阈值（秒）
SHORT_AUDIO_SECONDS: float = 3.0
RECOMMENDED_AUDIO_SECONDS: float = 10.0


def safe_stem(name: str) -> str:
    """把文件名清洗为安全分段，避免写入路径时越界。"""
    stem = Path(name).stem
    cleaned = "".join(c for c in stem if c.isalnum() or c in "-_.").strip()
    return cleaned or "audio"


def _extract_path(file_value: object) -> str | None:
    """兼容不同 gradio 版本 ``type="filepath"`` 的返回值（str / dict / Path）。"""
    if file_value is None:
        return None
    if isinstance(file_value, dict):
        return file_value.get("path")
    if isinstance(file_value, (str, Path)):
        return str(file_value)
    # 个别版本传入带 .name / .path 的对象
    for attr in ("path", "name"):
        value = getattr(file_value, attr, None)
        if isinstance(value, (str, Path)):
            return str(value)
    return None


def save_upload(src_path: str | Path, dest_dir: Path = UPLOADS_DIR) -> Path:
    """把上传的临时文件复制到工作空间，返回目标路径。

    Gradio 的上传文件在临时目录，重启即失效，必须持久化。同名文件追加序号，
    避免覆盖已有上传。
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    src = Path(src_path)
    suffix = src.suffix.lower() or ".wav"

    dest = dest_dir / f"{safe_stem(src.name)}{suffix}"
    counter = 1
    while dest.exists():
        dest = dest_dir / f"{safe_stem(src.name)}_{counter}{suffix}"
        counter += 1
    shutil.copy2(src, dest)
    return dest


def audio_metadata(path: str | Path) -> dict:
    """返回单个音频文件的展示用元数据。"""
    p = Path(path)
    duration = get_audio_duration(p)
    size = get_file_size(p)
    return {
        "path": str(p),
        "name": p.name,
        "duration_str": format_duration(duration),
        "size_str": format_size(size),
        "format": p.suffix.lstrip(".").upper() or "?",
        "status": "已上传",
    }


def find_upload(name: str, dest_dir: Path = UPLOADS_DIR) -> str | None:
    """按文件名在工作空间上传目录里查找完整路径，供预览播放用。"""
    if not name:
        return None
    path = Path(dest_dir) / Path(name).name
    return str(path) if path.is_file() else None


def process_uploaded_files(gr_files: list) -> tuple[list[list], str]:
    """处理一次上传批。

    Args:
        gr_files: Gradio ``File(file_count="multiple", type="filepath")`` 传回的列表。

    Returns:
        ``(table_rows, status_message)``；``table_rows`` 形如 ``[名称,时长,大小,格式,状态]``，
        ``status_message`` 汇总错误与告警，空串表示一切正常。
    """
    rows: list[list] = []
    messages: list[str] = []

    if not gr_files:
        return [], ""

    for file_value in gr_files:
        path = _extract_path(file_value)
        if not path:
            messages.append("⚠️ 收到无法识别的文件项，已跳过")
            continue

        ok, reason = validate_upload(path)
        if not ok:
            messages.append(f"✖ {Path(path).name}：{reason}")
            continue

        saved = save_upload(path)
        meta = audio_metadata(saved)

        if meta["duration_str"] == "0:00" or get_audio_duration(saved) < 0.0:
            # 无法解析时长的音频，仍入库但提示
            meta["status"] = "已上传(无法识别时长)"
        if get_audio_duration(saved) < SHORT_AUDIO_SECONDS:
            meta["status"] = "过短(<3s)"
            messages.append(
                f"⚠️ {saved.name}：时长 {meta['duration_str']}，建议 ≥{int(RECOMMENDED_AUDIO_SECONDS)}s"
            )

        rows.append([meta["name"], meta["duration_str"], meta["size_str"], meta["format"], meta["status"]])

    if rows:
        messages.insert(0, f"✅ 已上传 {len(rows)} 个文件。")

    return rows, "\n".join(messages)


def list_upload_rows(dest_dir: Path = UPLOADS_DIR) -> list[list]:
    """扫描工作空间上传目录，返回当前已存在的文件表格行。"""
    rows: list[list] = []
    root = Path(dest_dir)
    if not root.is_dir():
        return rows
    for p in sorted(root.iterdir()):
        if p.is_file() and p.suffix.lower() in SUPPORTED_AUDIO_FORMATS:
            meta = audio_metadata(p)
            rows.append([meta["name"], meta["duration_str"], meta["size_str"], meta["format"], meta["status"]])
    return rows


def list_upload_names(dest_dir: Path = UPLOADS_DIR) -> list[str]:
    """返回上传目录中现有音频文件名（供下拉框选择预览）。"""
    return sorted(p.name for p in Path(dest_dir).iterdir()
                  if p.is_file() and p.suffix.lower() in SUPPORTED_AUDIO_FORMATS)
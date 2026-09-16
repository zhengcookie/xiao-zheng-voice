"""工作空间目录布局与初始化。

所有运行期产生的数据都落在项目根目录的 ``workspace/`` 下，
便于备份、清理和理解「文件系统即数据存储」的设计。
"""

from __future__ import annotations

from pathlib import Path

from .utils import ensure_dir

#: 项目根目录（``src/`` 的上一级）
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

#: 工作空间根目录
WORKSPACE_DIR: Path = PROJECT_ROOT / "workspace"

#: 用户上传的原始音频
UPLOADS_DIR: Path = WORKSPACE_DIR / "uploads"

#: 预处理后的音频（切片 / 降噪）
PROCESSED_DIR: Path = WORKSPACE_DIR / "processed"

#: 训练好的模型，每个模型一个子目录
MODELS_DIR: Path = WORKSPACE_DIR / "models"

#: 合成的音频输出
OUTPUTS_DIR: Path = WORKSPACE_DIR / "outputs"

#: 需要保证存在的全部子目录
WORKSPACE_SUBDIRS: tuple[Path, ...] = (
    UPLOADS_DIR,
    PROCESSED_DIR,
    MODELS_DIR,
    OUTPUTS_DIR,
)


def init_workspace() -> dict[str, Path]:
    """创建 ``workspace/`` 及其子目录，幂等。

    Returns:
        目录名到 :class:`~pathlib.Path` 的映射，供 UI 展示与下游模块引用。
    """
    ensure_dir(WORKSPACE_DIR)
    for directory in WORKSPACE_SUBDIRS:
        ensure_dir(directory)

    return {
        "root": WORKSPACE_DIR,
        "uploads": UPLOADS_DIR,
        "processed": PROCESSED_DIR,
        "models": MODELS_DIR,
        "outputs": OUTPUTS_DIR,
    }


def workspace_summary() -> str:
    """返回一行工作空间路径摘要，用于状态栏显示。"""
    return f"📂 工作空间：{WORKSPACE_DIR}"

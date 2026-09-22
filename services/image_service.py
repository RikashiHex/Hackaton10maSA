"""Almacena fotografías fuera de SQLite para mantener la base ligera."""
from pathlib import Path
from shutil import copy2
from uuid import uuid4

ROOT_DIR = Path(__file__).resolve().parent.parent
IMAGE_DIR = ROOT_DIR / "assets" / "residuos"


def copy_image(source: str) -> str:
    if not source:
        return ""
    original = Path(source)
    if not original.exists():
        return ""
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    destination = IMAGE_DIR / f"{uuid4().hex}{original.suffix.lower()}"
    copy2(original, destination)
    return str(destination.relative_to(ROOT_DIR)).replace("\\", "/")


def full_image_path(relative_path: str) -> Path:
    return ROOT_DIR / relative_path if relative_path else Path()

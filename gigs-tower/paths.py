from pathlib import Path
import os

# gigs-tower/ 경로 (이 파일 위치 기준)
PROJECT_ROOT: Path = Path(__file__).resolve().parent

# 에셋 루트(폴더명)
IMAGE_DIR: Path = PROJECT_ROOT / "Image"
SOUND_DIR: Path = PROJECT_ROOT / "Sound"
FONT_DIR:  Path = PROJECT_ROOT / "Font"

def asset(*parts: str) -> str:
    """에셋 상대경로를 절대경로(str)로 변환 (OS 독립)"""
    return str(PROJECT_ROOT.joinpath(*parts))

def img(name: str) -> str:
    return str(IMAGE_DIR / name)

def snd(name: str) -> str:
    return str(SOUND_DIR / name)

def fnt(name: str) -> str:
    return str(FONT_DIR / name)
# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
    copy_metadata,
)

ROOT = Path(SPECPATH).resolve().parent


def safe_metadata(package_name: str):
    try:
        return copy_metadata(package_name)
    except Exception:
        return []


datas = [
    (str(ROOT / "ui"), "ui"),
    (str(ROOT / "assets"), "assets"),
]

# The release build prepares the multilingual model locally first so users do
# not face a 471 MB first-analysis download from Hugging Face.
model_root = ROOT / "runtime" / "models"
if model_root.exists():
    datas.append((str(model_root), "runtime/models"))

# Packages that use importlib.metadata or ship JSON/tokenizer resources need
# their package data/metadata preserved in the frozen build.
for distribution in (
    "sentence-transformers",
    "transformers",
    "huggingface-hub",
    "tokenizers",
    "safetensors",
    "scikit-learn",
):
    datas += safe_metadata(distribution)

for package in (
    "sentence_transformers",
    "transformers",
    "huggingface_hub",
):
    try:
        datas += collect_data_files(package, include_py_files=False)
    except Exception:
        pass

hiddenimports = [
    "webview",
    "webview.platforms.edgechromium",
    "clr",
    "pythonnet",
    "clr_loader",
    "pymupdf",
    "fitz",
    "docx",
    "openpyxl",
    "reportlab",
    "PIL",
    "sklearn",
    "scipy",
    "numpy",
    "torch",
    "tokenizers",
    "safetensors",
    "huggingface_hub",
    "transformers.models.auto",
    "transformers.models.bert.configuration_bert",
    "transformers.models.bert.modeling_bert",
    "transformers.models.bert.tokenization_bert",
    "transformers.models.bert.tokenization_bert_fast",
]

# sentence-transformers has several lazy imports that static analysis cannot
# reliably discover. Collect its Python modules explicitly while leaving huge
# unrelated ML frameworks (TensorFlow/JAX/etc.) excluded below.
try:
    hiddenimports += collect_submodules(
        "sentence_transformers",
        on_error="ignore",
    )
except Exception:
    pass

try:
    hiddenimports += collect_submodules(
        "transformers.models.bert",
        on_error="ignore",
    )
except Exception:
    pass

hiddenimports = sorted(set(hiddenimports))


a = Analysis(
    [str(ROOT / "src" / "main.py")],
    pathex=[str(ROOT / "src"), str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tensorflow",
        "tensorflow_intel",
        "jax",
        "jaxlib",
        "flax",
        "keras",
        "torchvision",
        "torchaudio",
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="JAM",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(ROOT / "assets" / "branding" / "jam_runtime.ico"),
    version=str(ROOT / "build" / "version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="JAM",
)

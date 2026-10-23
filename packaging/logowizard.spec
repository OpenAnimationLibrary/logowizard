# PyInstaller spec for the one-folder Windows build. Run from the repo root:
#   pyinstaller packaging/logowizard.spec --noconfirm
# Needs the fonts in local/fonts (logo-wizard-fonts) so they can be bundled.

from pathlib import Path
import runpy

from PyInstaller.utils.hooks import collect_all, collect_submodules

root = Path(SPECPATH).parent
fonts = root / "local" / "fonts"
release_fonts = runpy.run_path(str(root / "packaging" / "prepare_fonts.py"))["release_fonts"]
font_files = release_fonts(root)

datas = [
    (str(root / "data" / "fonts" / "manifest.csv"), "data/fonts"),
    (str(root / "data" / "palettes"), "data/palettes"),
    (str(root / "data" / "corpora" / "phrases.tsv"), "data/corpora"),
    (str(root / "src" / "logo_wizard" / "app" / "static"), "logo_wizard/app/static"),
]
for document in ("LICENSE", "DATA_LICENSES.md", "CREDITS.md"):
    if not (root / document).is_file():
        raise SystemExit(f"Required distribution notice is missing: {document}")
    datas.append((str(root / document), "."))
# Only manifest fonts and their licenses are distributed; cache extras stay behind.
for path in font_files:
    datas.append((str(path), f"fonts/{path.parent.name}"))

binaries = []
# The training side (PyTorch, Tesseract) is left out; the app runs the ONNX exports.
hiddenimports = collect_submodules("uvicorn") + collect_submodules(
    "logo_wizard", filter=lambda name: not name.startswith("logo_wizard.train")
)
for package in ("onnxruntime", "skia", "uharfbuzz"):
    d, b, h = collect_all(package)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    [str(root / "packaging" / "launcher.py")],
    pathex=[str(root / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["torch", "torchvision", "pytesseract", "matplotlib", "tkinter", "IPython", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LogoWizard",
    console=True,
    icon=str(root / "packaging" / "logowizard.ico"),
)
coll = COLLECT(exe, a.binaries, a.datas, name="LogoWizard")

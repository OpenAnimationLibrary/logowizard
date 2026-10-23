# Installing and training Logo Wizard on Windows

The packaged app runs immediately using its procedural title rules. Training is optional and takes place in a separate source checkout. Version 0.1.0 contains no trained weights; its ONNX model runtime uses the CPU.

## 1. Run the app

Download a package from the [Open Animation Library releases page](https://github.com/OpenAnimationLibrary/logowizard/releases).

### ZIP: no installation needed

Download `LogoWizard-0.1.0-win64.zip`, extract the entire archive, and double-click `LogoWizard.exe` inside the extracted `LogoWizard` folder. Keep the executable and its accompanying files together. Python, PyTorch and separate font downloads are not required.

A console opens and the app appears in your browser at `http://127.0.0.1:8765`, or the next available port. Close the console to stop the app.

### Optional installer

Run `LogoWizard-0.1.0-setup.exe` to install for your Windows user and create Start menu entries. The ZIP also includes an optional `install.ps1` for copying the extracted app into your user profile and adding a shortcut; running that script is not required to use the ZIP.

### Where your files go

| Files | Windows package | Source checkout |
| --- | --- | --- |
| Exported models and their JSON configuration | `%LOCALAPPDATA%\LogoWizard\models` | `local\models` |
| Feedback | `%LOCALAPPDATA%\LogoWizard\feedback` | `local\feedback` |
| Training datasets and checkpoints | Created by the source tools | `local\dataset` and `local\runs` |

The ZIP uses the same per-user data folder as the installer. Set the `LOGO_WIZARD_HOME` environment variable before starting the app or source tools to choose a different data root. Packaged fonts remain part of the app bundle.

## 2. Set up the optional training checkout

Install [Python 3.11](https://www.python.org/downloads/windows/) and [Git](https://git-scm.com/download/win). For dataset OCR filtering, install [Tesseract for Windows](https://github.com/UB-Mannheim/tesseract/wiki) and add it to PATH.

In PowerShell:

```powershell
git clone https://github.com/OpenAnimationLibrary/logowizard.git
cd logowizard
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cu126
.\.venv\Scripts\python.exe -m pip install -e ".[train,app,dev]"
.\.venv\Scripts\python.exe scripts\check_gpu.py
```

If you already created the source environment using the README, reuse that checkout and `.venv`. These commands call the environment directly, so activation is unnecessary. The project's existing GTX 1080 training setup uses the pinned PyTorch/CUDA combination above; run `check_gpu.py` to check the installed environment on your machine. The packaged app does not need this training setup.

The remaining commands assume you are in the source checkout. Keep its default `local/` data root while following the model-copy instructions below.

## 3. Build a dataset and train

The repository includes the corpus used by the generator. Download its fonts, benchmark a small sample, and then generate a dataset:

```powershell
.\.venv\Scripts\logo-wizard-fonts.exe
.\.venv\Scripts\logo-wizard-synth.exe --benchmark 100
.\.venv\Scripts\logo-wizard-synth.exe --count 250000
.\.venv\Scripts\logo-wizard-synth.exe --preview 64
```

`--count` is the number of attempted samples; filtering can keep fewer. Use a smaller count while trying the workflow. `--no-ocr` skips Tesseract filtering. Inspect the preview before starting a longer training run, and use the benchmark to estimate runtime on your hardware.

Train the layout model and, optionally, the stylizer:

```powershell
.\.venv\Scripts\logo-wizard-train-layout.exe --max-minutes 180
.\.venv\Scripts\logo-wizard-train-stylizer.exe --max-minutes 480
.\.venv\Scripts\logo-wizard-eval-stylizer.exe --n 200
```

The generator skips existing samples when resumed with the same settings. The trainers save checkpoints under `local\runs` and can resume by repeating their commands. A time budget stops a session; it does not mean training is complete. Check the saved previews, loss logs and evaluation results before using a model. The stylizer's default training resolution is 128 × 80; export upscales its finish to the requested output size.

## 4. Export models and give them to the app

Export the available checkpoints to ONNX:

```powershell
.\.venv\Scripts\logo-wizard-export-onnx.exe
$lwModels = Join-Path $env:LOCALAPPDATA "LogoWizard\models"
New-Item -ItemType Directory -Force -Path $lwModels | Out-Null
Copy-Item .\local\models\* -Destination $lwModels -Force
```

The exporter writes `layout.onnx` with `layout.json` and, when stylizer weights exist, `stylizer.onnx` with `stylizer.json`. Each model needs its matching JSON file. You can use the layout model without training a stylizer.

Restart the app after copying. Its status shows `layout model (ONNX)` when the layout model loads successfully. The Windows package runs these models on CPU; this release does not provide DirectML GPU acceleration. A source environment with PyTorch installed can also use checkpoints from `local\runs` when ONNX exports are absent.

## 5. Fine-tune from your feedback

The Create tab records thumbs up/down and exports. With a trained layout model available, the Blind test tab records your choices between model and procedural suggestions. After collecting at least 20 usable feedback examples, run:

```powershell
$lwFeedback = Join-Path $env:LOCALAPPDATA "LogoWizard\feedback\feedback.jsonl"
.\.venv\Scripts\logo-wizard-finetune-layout.exe --feedback $lwFeedback
.\.venv\Scripts\logo-wizard-export-onnx.exe
$lwModels = Join-Path $env:LOCALAPPDATA "LogoWizard\models"
New-Item -ItemType Directory -Force -Path $lwModels | Out-Null
Copy-Item .\local\models\layout.* -Destination $lwModels -Force
```

Fine-tuning requires the original layout checkpoint in the training checkout. Export again before copying so the app receives the updated weights, then restart it. The previous checkpoint is kept as `local\runs\layout\best.before-feedback.pt`; to restore it, replace `best.pt` with that backup, export again, and copy the refreshed ONNX files.

## Build the Windows packages yourself

From a source checkout on Windows with Python 3.11:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1
```

The build produces `dist\LogoWizard\` and `dist\LogoWizard-0.1.0-win64.zip`. With [Inno Setup 6](https://jrsoftware.org/isinfo.php) installed, it also creates `dist\LogoWizard-0.1.0-setup.exe`. The packages include the fonts and their license files, the app runtime and procedural data; trained weights are supplied separately.

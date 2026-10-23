# Credits and source provenance

## Project

Logo Wizard was developed by **Rodney Baker with Claude assistance**. The imported source history records Rodney and Claude as commit authors and includes Claude co-author credit. This public edition is maintained under [Open Animation Library](https://github.com/OpenAnimationLibrary/logowizard).

The application and packaging were imported as snapshots into an independent repository. The original Git history and GitHub fork relationship were not copied, and changes are not synchronized automatically. The references below preserve the origin of the work.

| Component | Source |
| --- | --- |
| Core application, renderer, corpus and model tools | [RodneyBaker/logowizard PR #7](https://github.com/RodneyBaker/logowizard/pull/7), head [`13171c1136bd12b92edbbef7211598c1f2b3097f`](https://github.com/RodneyBaker/logowizard/commit/13171c1136bd12b92edbbef7211598c1f2b3097f) |
| Windows packaging and installation/release documentation | Adapted from later source commit [`1c7f6acdb84342ffbe4611a2a79ddc44a67b9b19`](https://github.com/RodneyBaker/logowizard/commit/1c7f6acdb84342ffbe4611a2a79ddc44a67b9b19) |

The local [design plan](docs/design-plan.md) preserves the project's architecture and goals without depending on a separate chat or artifact.

## Licenses and dependencies

Project code is distributed under the existing [BSD 3-Clause license](LICENSE) of this repository. External fonts, data and software retain their own licenses.

- **Fonts:** Google Fonts families under SIL Open Font License 1.1, Apache License 2.0 or Ubuntu Font License 1.0. The font manifest records each face's source and checksum; packaged fonts include their corresponding license texts.
- **Text sources:** the King James Bible and Webster's 1913 through Project Gutenberg, Project Gutenberg catalog titles, and US Census name lists. Source URLs and license notes are recorded in [DATA_LICENSES.md](DATA_LICENSES.md).
- **Core software:** HarfBuzz/uharfbuzz, Skia/skia-python, NumPy, Pillow, PyYAML, FastAPI, Uvicorn and ONNX Runtime support the application. Optional training uses PyTorch, ONNX and Tesseract/pytesseract. Windows packaging uses PyInstaller and Inno Setup.

See [pyproject.toml](pyproject.toml) for the project's dependency declarations and [DATA_LICENSES.md](DATA_LICENSES.md) for its font and data inventory.

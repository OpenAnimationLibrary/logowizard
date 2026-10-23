# Changelog

## 0.1.0

First public release of the independently hosted Open Animation Library edition.

- **Create and refine title logos:** enter a title, style words and optional subtitle; generate candidates; adjust fonts, palettes, arrangement, warp, outlines, shadow, extrusion, fill and texture.
- **Export:** save PNG at 512, 1024 or 2048 pixels wide, or save the design specification as JSON.
- **Procedural generation:** font-based lettering and title rules work immediately on CPU. No trained model is needed for this mode.
- **Fonts and effects:** bundled Google Fonts with their license texts; arch, valley, bulge, wave, perspective, fan and stagger warps; stacked outlines, gradients, foil, inline highlights, halftone and distressed textures.
- **Optional models:** source tools generate synthetic training data, train a layout model and diffusion stylizer, and export them to ONNX. The packaged app supports those exports through ONNX Runtime on CPU.
- **Feedback:** local thumbs up/down, exports and Blind test choices can be used for explicit layout-model fine-tuning in the source checkout.
- **Windows distribution:** a ZIP that runs after extraction and an optional per-user installer. Python and PyTorch are not needed to run the packaged app.
- **Independent project:** application snapshot from PR #7, with later Windows packaging adapted for this repository. Exact source revisions and credits are recorded in [CREDITS.md](CREDITS.md).

### Release limits

No trained weights are bundled. Model suggestions and the diffusion finish require separately trained and exported models. Training tools and PyTorch are supplied through the source workflow, not the Windows executable. Packaged ONNX inference uses CPU; DirectML acceleration is not included in this release. The stylizer's default resolution is 128 × 80 pixels and its output is upscaled for export. Feedback does not retrain models automatically.

See [INSTALL.md](INSTALL.md) for installation, training, model export and feedback instructions.

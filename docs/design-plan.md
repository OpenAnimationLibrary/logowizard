# Design plan

This document is the local design reference for the Open Animation Library edition of Logo Wizard. It carries forward the original project decisions recorded on 2026-10-22. [CREDITS.md](../CREDITS.md) identifies the source snapshots and contributors; [INSTALL.md](../INSTALL.md) describes the current runnable workflows.

## Architecture

- **Procedural rendering:** shape lettering with HarfBuzz and draw it with Skia. Title rules choose fonts, palettes, arrangement and effects. This path works on CPU without trained weights.
- **Optional layout model:** read the title and style words and propose a JSON design specification. The renderer draws the chosen specification using font outlines.
- **Optional stylizer:** train a small diffusion model on synthetic examples, conditioned on the lettering mask and design. The default training resolution is 128 × 80 pixels, with upscaling for export.
- **Local operation:** the app opens a browser interface served by a local process. Datasets, checkpoints, model exports and feedback remain in the configured local data directory.
- **Output:** text-based comic-book and novel-cover logos as raster PNG, with editable design specifications saved as JSON. Emblem generation is outside the original scope.

## Data and training

The project uses a curated Google Fonts catalog and text lists derived from the sources documented in [DATA_LICENSES.md](../DATA_LICENSES.md). Its procedural renderer produces the synthetic examples used for model training.

The original training target was a Windows PC with a GTX 1080 (8 GB), i5-9400F and 16 GB RAM, using fp32 training. This is a development target, not a requirement to use the procedural app. Benchmark and evaluate model training on the machine where it will run.

## Development stages

1. Corpus builders and provenance.
2. Font manifest, renderer and procedural app.
3. Synthetic dataset generation, filtering and previews.
4. Layout-model training and comparison with procedural suggestions.
5. Stylizer training and readability evaluation.
6. App refinement, feedback and ONNX export.
7. Windows packaging and release verification.

The source contains these workflows, but version 0.1.0 ships without trained weights. Its packaged ONNX runtime uses CPU. Feedback-driven fine-tuning remains an explicit source-tool step, followed by exporting and copying the updated model into the app.

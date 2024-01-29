# EasyOCR-wrapper

## Description

Wrapper for [EasyOCR](https://github.com/JaidedAI/EasyOCR?tab=readme-ov-file) end-to-end text detection and recognition.
The wrapper takes a [`VideoDocument`]('http://mmif.clams.ai/vocabulary/VideoDocument/v1') with SWT 
[`TimeFrame`]('http://mmif.clams.ai/vocabulary/TimeFrame/v1') annotations and 
returns [`BoundingBox`]('http://mmif.clams.ai/vocabulary/BoundingBox/v1') and 
[`TextDocument`]('http://mmif.clams.ai/vocabulary/TextDocument/v1') [aligned]('http://mmif.clams.ai/vocabulary/Alignment/v1') 
with [`TimePoint`]('http://mmif.clams.ai/vocabulary/TimePoint/v1') annotations from the middle frame of each TimeFrame.

EasyOCR seems to handle reading order, but there isn't much documentation regarding the implementation. Regardless,
the `BoundingBoxes` and `TextDocuments` are ordered within each `TimePoint` so reading order can be inferred from the
annotation ids.

Here's the framework from the EasyOCR repo:
![EasyOCR Framework](https://github.com/JaidedAI/EasyOCR/raw/master/examples/easyocr_framework.jpeg)

## User instruction

General user instructions for CLAMS apps is available at [CLAMS Apps documentation](https://apps.clams.ai/clamsapp).

### System requirements

- Requires mmif-python[cv] for the `VideoDocument` helper functions
- Requires GPU to run at a reasonable speed

### Configurable runtime parameter

For the full list of parameters, please refer to the app metadata from [CLAMS App Directory](https://apps.clams.ai) or [`metadata.py`](metadata.py) file in this repository.
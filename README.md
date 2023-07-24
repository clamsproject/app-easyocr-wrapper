# EasyOCR Wrapper

## Description

Runs EasyOCR on timeframes from a video document.

## User instruction

General user instructions for CLAMS apps is available at [CLAMS Apps documentation](https://apps.clams.ai/clamsapp).

### System requirements

> **note**
> TO_DEVS: Any system-level software required to run this app. Usually include some of the following:
> * supported OS and CPU architectures
> * usage of GPU
> * system package names (e.g. `ffmpeg`, `libav`, `libopencv-dev`, etc.)
> * some example code snippet to install them on Debian/Ubuntu (because our base images are based on Debian)
>     * e.g. `apt-get update && apt-get install -y <package-name>`

### Configurable runtime parameter

Although all CLAMS apps are supposed to run as *stateless* HTTP servers, some apps can configured at request time using [URL query strings](https://en.wikipedia.org/wiki/Query_string). For runtime parameter supported by this app, please visit [CLAMS App Directory](https://apps.clams.ai) and look for the app name and version. 

> **warning**
> TO_DEVS: If you're not developing this app for publishing on the CLAMS App Directory, the above paragraph is not applicable. Feel free to delete or change it.

> **note**
> TO_DEVS: all runtime parameters are supported to be VERY METICULOUSLY documented in the app's `metadata.py` file. However for some reason, if you need to use this space to elaborate what's already documented in `metadata.py`, feel free to do so.
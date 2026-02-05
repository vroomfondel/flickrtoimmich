# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**flickrtoimmich** is a Docker/Podman-based tool for backing up Flickr photo libraries and optionally uploading them to Immich. It wraps the `flickr_download` library with browser-based OAuth authentication support in containerized environments.

Key capabilities:
- Downloads photos/videos from Flickr with full metadata preservation (EXIF, JSON)
- Handles OAuth via browser (X11 forwarding, domain socket, or D-Bus modes)
- Intelligent rate-limit handling with exponential backoff and process suspension
- Resumable downloads via API response caching
- Optional upload to Immich photo management system
- Multi-architecture Docker images (amd64 + arm64)

## Build and Development Commands

```bash
# Install dependencies (creates venv)
make install

# Code quality
make lint                 # Black formatter (line length: 120)
make isort                # Sort imports
make tcheck               # MyPy type checking (strict mode)
make gitleaks             # Scan for secrets

# Testing
make tests                # Run pytest
make prepare              # Run tests + commit-checks

# Pre-commit hooks
make commit-checks        # Run all pre-commit hooks

# Docker
make build                # Build Docker image
make dstart               # Launch interactive container with volumes
./build_multiarch.sh      # Build multi-arch and push
./build_multiarch.sh onlylocal  # Build locally without push
```

## Container Runtime Commands

Via `flickr-docker.sh`:
```bash
./flickr-docker.sh auth              # OAuth authentication
./flickr-docker.sh download <user>   # Download all albums
./flickr-docker.sh album <id>        # Download single album
./flickr-docker.sh list <user>       # List albums
./flickr-docker.sh shell             # Interactive shell
./flickr-docker.sh test-browser      # Test X11/browser setup
```

## Architecture

### Project Structure
```
flickrtoimmich/
├── flickrtoimmich/          # Python package
│   ├── __init__.py          # Version (0.1.0)
│   ├── download_wrapper.py  # Monkeypatch for flickr_download date handling
│   ├── list_albums.py       # Album listing with photo/video counts
│   ├── immich_uploader.py   # Batched Immich uploader
│   └── py.typed             # PEP 561 type marker
├── tests/                   # Test suite
│   └── test_base.py         # Basic sanity tests
└── [shell scripts]          # Docker/runtime scripts
```

### Browser Authentication Modes
Three mutually exclusive modes for OAuth in containers:
1. **X11 Mode**: Display forwarding with xauth cookies
2. **Domain Socket Mode** (`USE_DSOCKET`): Unix socket IPC via `url-opener`
3. **D-Bus Mode** (`USE_DBUS`): XDG Desktop Portal via `url-dbus-opener`

### Rate Limit Handling
- Process supervision with SIGSTOP/SIGCONT signals
- Exponential backoff with configurable base/max
- `EXIT_ON_RATE_LIMIT=1` for CI/K8s environments (immediate exit instead of wait)

### Monkey Patching Strategy
The project patches `flickr_download` for invalid date handling:
1. Dockerfile `sed` patches during image build
2. Runtime monkeypatch in `flickr-download-wrapper.py` for `utils.set_file_time`

### Key Scripts
- `flickr-docker.sh` - Main orchestration (auth, download, upload routing)
- `flickr-download-wrapper.py` - Wraps flickr_download with date handling fixes
- `immich-uploader-wrapped.py` - Batched Immich uploader with retry logic
- `url-opener` / `url-dbus-opener` - Browser URL forwarding for container auth

### Runtime Detection
Detects environment via:
- Docker: `/.dockerenv`
- Podman: `/run/.containerenv`
- Kubernetes: `KUBERNETES_SERVICE_HOST` env var
- Configurable home: `FLICKR_HOME` env var

## Code Style

- **Line length**: 120 characters (Black)
- **Type checking**: MyPy strict mode (`disallow_untyped_defs`, `check_untyped_defs`)
- **Logging**: Loguru with colored output, controlled by `LOGURU_LEVEL`
- **Python version**: 3.14

## Runtime Directories

Created at runtime (not in repo):
- `flickr-backup/` - Downloaded photos and JSON metadata
- `flickr-config/` - API credentials and OAuth tokens
- `flickr-cache/` - API response cache for resumable downloads

## Docker Build

Base image: `python:3.14-slim` with Chromium, Firefox ESR, ExifTool, and `@immich/cli`.

Build auto-detects Docker vs Podman:
- Docker: Uses buildx with binfmt for cross-compilation
- Podman: Creates manifest with per-platform builds using VM emulation

Credentials sourced from `scripts/include.sh` (not committed).

#!/bin/bash
# Ensure HOME directory exists and is writable
if [ ! -d "$HOME" ]; then
    mkdir -p "$HOME" 2>/dev/null || true
fi
# Mozilla directory for Firefox
mkdir -p "$HOME/.mozilla" 2>/dev/null || true

echo BUILDTIME: $BUILDTIME

# Parse --dry-run flag
DRY_RUN=false
args=()
for arg in "$@"; do
    if [ "$arg" = "--dry-run" ]; then
        DRY_RUN=true
    else
        args+=("$arg")
    fi
done
set -- "${args[@]}"

if [ "$DRY_RUN" = true ]; then
    echo "[DRY-RUN] Dry-run mode enabled — no commands will be executed."
fi

if [ "$1" = "--help" ] || [ "$1" = "-h" ] || [ $# -eq 0 ]; then
    cat <<'EOF'
Usage: entrypoint.sh [--dry-run] <command> [args...]

Commands:
  shell [cmd...]                  Open an interactive shell (or run cmd)
  download_then_upload <user>     Download all albums, then upload to Immich
  upload                          Upload existing downloads to Immich
  <flickr-docker.sh args...>      Pass through to flickr-docker.sh
                                  (e.g. auth, download <user>, album <id>, list <user>)

Options:
  --dry-run    Show what would be done without executing downloads or uploads

Required environment variables (for upload/download_then_upload):
  DATA_DIR              Path to the data directory
  IMMICH_API_KEY        Immich API key
  IMMICH_INSTANCE_URL   Immich instance URL
EOF
    exit 0
fi

if [ "$1" = "shell" ]; then
    shift
    if [ $# -eq 0 ]; then
        exec /bin/bash
    else
        exec /bin/bash "$@"
    fi
elif [ "$1" = "download_then_upload" ]; then
    for var in DATA_DIR IMMICH_API_KEY IMMICH_INSTANCE_URL; do
        if [ -z "${!var}" ]; then
            echo "ERROR: Required environment variable $var is not set" >&2
            exit 1
        fi
    done

    /usr/local/bin/flickr-docker.sh info

    if [ "$DRY_RUN" = true ]; then
        echo "[DRY-RUN] /usr/local/bin/flickr-docker.sh download ${*:2}"
        /usr/local/bin/upload-to-immich.sh --dry-run
        rc_upload=$?
        echo rc_upload: $rc_upload
        exit $rc_upload
    fi

    /usr/local/bin/flickr-docker.sh download "${@:2}"
    rc_download=$?
    echo rc_download: $rc_download
    /usr/local/bin/upload-to-immich.sh
    rc_upload=$?
    echo rc_upload: $rc_upload
    exit $(( rc_download > rc_upload ? rc_download : rc_upload ))
elif [ "$1" = "upload" ]; then
    for var in DATA_DIR IMMICH_API_KEY IMMICH_INSTANCE_URL; do
        if [ -z "${!var}" ]; then
            echo "ERROR: Required environment variable $var is not set" >&2
            exit 1
        fi
    done

    if [ "$DRY_RUN" = true ]; then
        /usr/local/bin/upload-to-immich.sh --dry-run
    else
        /usr/local/bin/upload-to-immich.sh
    fi
    rc_upload=$?
    echo rc_upload: $rc_upload
    exit $rc_upload
else
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY-RUN] /usr/local/bin/flickr-docker.sh info"
        echo "[DRY-RUN] /usr/local/bin/flickr-docker.sh $*"
        exit 0
    fi
    /usr/local/bin/flickr-docker.sh info &&
    exec /usr/local/bin/flickr-docker.sh "$@"
fi

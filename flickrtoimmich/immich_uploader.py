#!/usr/bin/env python3
"""Batched Immich uploader with streaming output."""

import argparse
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import IO


def stream_pipe(pipe: IO[str], target: IO[str]) -> None:
    for line in pipe:
        target.write(line)
    pipe.close()


def upload_batch(files: list[Path], album: str) -> bool:
    cmd = ["immich", "upload", *[str(f) for f in files], "--album", album]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    t_out = threading.Thread(target=stream_pipe, args=(proc.stdout, sys.stdout))
    t_err = threading.Thread(target=stream_pipe, args=(proc.stderr, sys.stderr))
    t_out.start()
    t_err.start()
    t_out.join()
    t_err.join()

    rc = proc.wait()
    if rc != 0:
        print(f"ERROR: immich upload exited with code {rc}", file=sys.stderr)
    return rc == 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload photos/videos to Immich in batches")
    parser.add_argument("--batch-size", type=int, default=20, help="number of files per upload batch (default: 20)")
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=[".jpg", ".jpeg", ".png", ".mp4"],
        help="file extensions to include (default: .jpg .jpeg .png .mp4)",
    )
    parser.add_argument("--dry-run", action="store_true", help="list files that would be uploaded without uploading")
    return parser.parse_args()


def main(batch_size: int, extensions: set[str], dry_run: bool = False) -> None:
    data_dir = Path(os.environ.get("DATA_DIR", "."))

    print("START")

    for album_dir in sorted(data_dir.iterdir()):
        if not album_dir.is_dir():
            continue
        album = album_dir.name
        files = sorted(f for f in album_dir.rglob("*") if f.is_file() and f.suffix.lower() in extensions)
        if not files:
            continue

        if dry_run:
            print(f"[DRY-RUN] Album '{album}': {len(files)} file(s)")
            for f in files:
                print(f"[DRY-RUN]   {f}")
        else:
            print(f"Album '{album}': {len(files)} file(s)")
            for i in range(0, len(files), batch_size):
                batch = files[i : i + batch_size]
                upload_batch(batch, album)

    print()
    print("DONE")


def cli() -> None:
    args = parse_args()
    main(batch_size=args.batch_size, extensions=set(args.extensions), dry_run=args.dry_run)


if __name__ == "__main__":
    cli()

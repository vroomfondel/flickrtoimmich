#!/usr/bin/env python3
"""Batched Immich uploader with streaming output."""

import argparse
import os
import subprocess
import sys
import threading
from datetime import datetime, timezone
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


def _fmt_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}" if unit != "B" else f"{size} B"
        size_f = size / 1024
        size = int(size_f)  # only for the loop; final return uses float
    return f"{size / 1024:.1f} TB"


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

    # Collect all albums and files first for total counts
    albums: list[tuple[str, list[Path]]] = []
    for album_dir in sorted(data_dir.iterdir()):
        if not album_dir.is_dir():
            continue
        files = sorted(f for f in album_dir.rglob("*") if f.is_file() and f.suffix.lower() in extensions)
        if files:
            albums.append((album_dir.name, files))

    total_files = sum(len(files) for _, files in albums)
    total_batches = sum((len(files) + batch_size - 1) // batch_size for _, files in albums)
    total_size = 0
    prefix = "[DRY-RUN] " if dry_run else ""
    file_nr = 0
    global_batch_nr = 0
    num_albums = len(albums)

    for album_nr, (album, files) in enumerate(albums, 1):
        num_batches = (len(files) + batch_size - 1) // batch_size
        album_size = sum(f.stat().st_size for f in files) if dry_run else 0
        if dry_run:
            total_size += album_size
            print(
                f"{prefix}Album {album_nr}/{num_albums} '{album}':"
                f" {len(files)} file(s), {_fmt_size(album_size)}, {num_batches} batch(es)"
            )
        else:
            print(f"Album {album_nr}/{num_albums} '{album}': {len(files)} file(s), {num_batches} batch(es)")

        for batch_idx in range(0, len(files), batch_size):
            batch = files[batch_idx : batch_idx + batch_size]
            batch_nr = batch_idx // batch_size + 1
            global_batch_nr += 1
            print(
                f"{prefix}  Batch {batch_nr}/{num_batches} [{global_batch_nr}/{total_batches}] ({len(batch)} file(s))"
            )

            for idx_in_batch, f in enumerate(batch, 1):
                file_nr += 1
                if dry_run:
                    stat = f.stat()
                    mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    print(
                        f"{prefix}    [{file_nr}/{total_files}] batch:{idx_in_batch}/{len(batch)}"
                        f"  {f}  ({_fmt_size(stat.st_size)}, {mtime})"
                    )
                else:
                    print(f"    [{file_nr}/{total_files}] batch:{idx_in_batch}/{len(batch)}  {f}")

            if not dry_run:
                upload_batch(batch, album)

    if dry_run:
        print()
        print(f"{prefix}Total: {len(albums)} album(s), {total_files} file(s), {_fmt_size(total_size)}")

    print()
    print("DONE")


def cli() -> None:
    from flickrtoimmich import startup

    startup()
    args = parse_args()
    main(batch_size=args.batch_size, extensions=set(args.extensions), dry_run=args.dry_run)


if __name__ == "__main__":
    cli()

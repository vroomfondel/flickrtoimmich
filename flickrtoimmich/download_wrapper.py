#!/usr/bin/env python3
"""Wrapper for flickr_download that patches set_file_time for unknown dates."""

import flickr_download.utils as _u

_orig = _u.set_file_time


def _safe(fname: str, taken_str: str) -> None:
    """Set file modification time, skipping invalid or unknown date strings.

    Args:
        fname: Path to the file whose modification time should be updated.
        taken_str: Date-taken string from Flickr metadata (e.g. ``"2024-01-15 12:30:00"``).
    """
    if not taken_str or taken_str.startswith("0000"):
        return
    _orig(fname, taken_str)


_u.set_file_time = _safe

from flickr_download.flick_download import main as _flickr_main


def main() -> None:
    """Entry point for flickr-download-wrapper console script."""
    _flickr_main()


if __name__ == "__main__":
    main()

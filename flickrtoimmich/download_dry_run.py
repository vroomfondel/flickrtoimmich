"""Dry-run mode for Flickr downloads — lists albums and photos without downloading."""

import argparse
import os
import sys

import flickr_api
import yaml
from flickr_api.auth import AuthHandler
from loguru import logger


def _load_flickr_api() -> None:
    """Load Flickr API credentials and OAuth token from config files."""
    config_path = os.path.join(os.environ.get("HOME", os.path.expanduser("~")), ".flickr_download")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    flickr_api.set_keys(api_key=config["api_key"], api_secret=config["api_secret"])

    token_path = os.path.join(os.environ.get("HOME", os.path.expanduser("~")), ".flickr_token")
    if os.path.exists(token_path):
        flickr_api.set_auth_handler(AuthHandler.load(token_path))


def _list_album_photos(ps: flickr_api.Photoset) -> int:
    """List individual photos/videos in an album.

    Args:
        ps: Flickr photoset object.

    Returns:
        Number of files listed.
    """
    count = 0
    for photo in ps.getPhotos():
        count += 1
        media = getattr(photo, "media", "photo")
        logger.info(f"[DRY-RUN]   [{count}] {photo.title} ({media})")
    return count


def dry_run_user(user_url: str, verbose: bool = False) -> None:
    """List all albums and their photos for a Flickr user without downloading.

    Args:
        user_url: Flickr user URL (e.g. "https://www.flickr.com/photos/username").
        verbose: If True, list individual photos per album.
    """
    _load_flickr_api()
    user = flickr_api.Person.findByUrl(user_url)
    logger.info(f"[DRY-RUN] User: {user.username}")

    total_photos = 0
    total_videos = 0
    album_nr = 0

    for ps in user.getPhotosets():
        album_nr += 1
        photos = int(getattr(ps, "photos", 0))
        videos = int(getattr(ps, "videos", 0))
        total_photos += photos
        total_videos += videos
        logger.info(f"[DRY-RUN] Album {album_nr}: '{ps.title}' — {photos} photo(s), {videos} video(s)")
        if verbose:
            _list_album_photos(ps)

    logger.info(f"[DRY-RUN] Total: {album_nr} album(s), {total_photos} photo(s), {total_videos} video(s)")


def dry_run_album(album_id: str) -> None:
    """List photos in a single Flickr album without downloading.

    Args:
        album_id: Flickr photoset/album ID.
    """
    _load_flickr_api()
    ps = flickr_api.Photoset(id=album_id)
    ps.getInfo()
    logger.info(f"[DRY-RUN] Album: '{ps.title}' (ID: {album_id})")

    count = _list_album_photos(ps)
    logger.info(f"[DRY-RUN] Total: {count} file(s) in album")


def main() -> None:
    """CLI entry point for download dry-run."""
    from flickrtoimmich import startup

    startup()

    parser = argparse.ArgumentParser(description="Dry-run mode for Flickr downloads")
    sub = parser.add_subparsers(dest="mode", required=True)

    user_parser = sub.add_parser("user", help="List all albums for a user")
    user_parser.add_argument("url", help="Flickr user URL")
    user_parser.add_argument("-v", "--verbose", action="store_true", help="list individual photos per album")

    album_parser = sub.add_parser("album", help="List photos in an album")
    album_parser.add_argument("album_id", help="Flickr album/photoset ID")

    args = parser.parse_args()

    if args.mode == "user":
        dry_run_user(args.url, verbose=args.verbose)
    elif args.mode == "album":
        dry_run_album(args.album_id)


if __name__ == "__main__":
    main()

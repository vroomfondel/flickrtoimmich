"""Basic sanity tests for flickrtoimmich."""

import flickrtoimmich


def test_version_exists() -> None:
    """Verify that the package has a version string."""
    assert hasattr(flickrtoimmich, "__version__")
    assert isinstance(flickrtoimmich.__version__, str)
    assert len(flickrtoimmich.__version__) > 0


def test_version_format() -> None:
    """Verify version follows semver pattern."""
    version = flickrtoimmich.__version__
    parts = version.split(".")
    assert len(parts) >= 2, "Version should have at least major.minor"
    for part in parts:
        assert part.isdigit() or part[0].isdigit(), f"Version part '{part}' should start with a digit"


def test_package_imports() -> None:
    """Verify that package modules can be imported."""
    from flickrtoimmich import immich_uploader

    assert hasattr(immich_uploader, "main")
    assert hasattr(immich_uploader, "upload_batch")

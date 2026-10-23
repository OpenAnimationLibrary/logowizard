"""Fetch and verify the exact font files listed in the committed manifest.

The release bundles only those files and their family licenses. Unlike the
development font updater, this script never rewrites the manifest.
"""

import argparse
import csv
import hashlib
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath


LICENSE_FILES = {
    "SIL OFL 1.1": "OFL.txt",
    "Apache 2.0": "LICENSE.txt",
    "Ubuntu Font License 1.0": "UFL.txt",
}


def release_fonts(root: Path, download: bool = False) -> list[Path]:
    """Return the validated font/license files, fetching missing files if asked."""
    font_dir = root / "local" / "fonts"
    with (root / "data" / "fonts" / "manifest.csv").open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    if not rows:
        raise ValueError("The font manifest is empty.")

    files: dict[Path, tuple[str, str | None]] = {}
    families = set()
    for row in rows:
        relative = PurePosixPath(row["file"])
        if len(relative.parts) != 2 or relative.parts[0] != row["dirname"] or ".." in relative.parts:
            raise ValueError(f"Invalid font path in manifest: {row['file']}")
        if relative.suffix.lower() not in (".ttf", ".otf"):
            raise ValueError(f"Unsupported font file: {relative}")
        expected = row["sha256"].lower()
        if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
            raise ValueError(f"Invalid SHA-256 for {relative}")
        source_url = row["source_url"]
        parsed = urllib.parse.urlsplit(source_url)
        if parsed.scheme != "https" or parsed.netloc != "raw.githubusercontent.com":
            raise ValueError(f"Unexpected font source: {source_url}")
        path = font_dir.joinpath(*relative.parts)
        entry = (source_url, expected)
        if path in files and files[path] != entry:
            raise ValueError(f"Conflicting manifest entries for {relative}")
        files[path] = entry
        license_name = LICENSE_FILES[row["license"]]
        license_path = path.parent / license_name
        license_entry = (source_url.rsplit("/", 1)[0] + "/" + license_name, None)
        if license_path in files and files[license_path] != license_entry:
            raise ValueError(f"Conflicting license entries for {row['dirname']}")
        files[license_path] = license_entry
        families.add(row["dirname"])

    def ensure(item: tuple[Path, tuple[str, str | None]]) -> None:
        path, (url, expected) = item
        data = path.read_bytes() if path.is_file() else b""
        valid = bool(data) and (expected is None or hashlib.sha256(data).hexdigest() == expected)
        if not valid and download:
            request = urllib.request.Request(
                urllib.parse.quote(url, safe=":/%"),
                headers={"User-Agent": "LogoWizard-release/0.1"},
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                data = response.read()
            if not data or (expected is not None and hashlib.sha256(data).hexdigest() != expected):
                raise ValueError(f"Downloaded file does not match the manifest: {path.relative_to(font_dir)}")
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_name(path.name + ".download")
            temporary.write_bytes(data)
            temporary.replace(path)
            valid = True
        if not valid:
            raise ValueError(f"Missing or invalid font/license file: {path.relative_to(font_dir)}")
        if expected is None:
            data.decode("utf-8-sig")  # License files must be readable notices, not binary placeholders.

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(ensure, files.items()))
    print(f"Verified {len(rows)} faces in {len(families)} font families, including their license files.")
    return sorted(files)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="download missing or mismatched files")
    args = parser.parse_args()
    release_fonts(Path(__file__).resolve().parents[1], download=args.download)


if __name__ == "__main__":
    main()

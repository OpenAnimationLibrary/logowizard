"""Complete the existing, empty OAL v0.1.0 release after the Windows smoke test.

This one-time path runs only on the deliberately created release/v0.1.0 branch.
It preserves the release title/body and never replaces existing release assets.
"""

import hashlib
import json
import os
import subprocess
import tomllib
import urllib.request
from pathlib import Path


REPOSITORY = "OpenAnimationLibrary/logowizard"
TAG = "v0.1.0"
RELEASE_ID = 421429341
INITIAL_SHA = "28cf4f79188089ea21c8a58d6ba712d4725edfa4"
ASSET_NAMES = ("LogoWizard-0.1.0-win64.zip", "LogoWizard-0.1.0-setup.exe")


def main() -> None:
    if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY:
        raise RuntimeError("This completion step is restricted to the OAL LogoWizard repository.")
    if os.environ.get("GITHUB_EVENT_NAME") != "push" or os.environ.get("GITHUB_REF") != "refs/heads/release/v0.1.0":
        raise RuntimeError("This completion step requires a push to release/v0.1.0.")
    sha = os.environ["GITHUB_SHA"]
    if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha) or sha == INITIAL_SHA:
        raise RuntimeError("The build commit must be a complete source commit.")
    root = Path(__file__).resolve().parents[1]
    with (root / "pyproject.toml").open("rb") as source:
        if tomllib.load(source)["project"]["version"] != "0.1.0":
            raise RuntimeError("This completion step only publishes version 0.1.0.")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if head != sha:
        raise RuntimeError("The checkout differs from the commit that triggered this build.")
    token = os.environ["GITHUB_TOKEN"]
    api_base = f"https://api.github.com/repos/{REPOSITORY}"

    def request(url: str, data: bytes | None = None, content_type: str = "application/json"):
        req = urllib.request.Request(url, data=data, headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": content_type,
            "User-Agent": "LogoWizard-first-release",
            "Cache-Control": "no-cache",
        })
        with urllib.request.urlopen(req, timeout=300) as response:
            return json.load(response)

    def release_guard(expected_assets: set[int]):
        release = request(f"{api_base}/releases/{RELEASE_ID}")
        if release["id"] != RELEASE_ID or release["tag_name"] != TAG or release["draft"]:
            raise RuntimeError("The expected published release is no longer available.")
        if release.get("immutable") is not False:
            raise RuntimeError("The release is immutable or its mutability could not be verified.")
        assets = request(f"{api_base}/releases/{RELEASE_ID}/assets?per_page=100")
        if {asset["id"] for asset in assets} != expected_assets:
            raise RuntimeError("The release has existing or unexpectedly changed assets; nothing will be overwritten.")
        return release

    def tag_guard(allowed: set[str]) -> str:
        ref = request(f"{api_base}/git/ref/tags/{TAG}")
        if ref["object"]["type"] != "commit" or ref["object"]["sha"] not in allowed:
            raise RuntimeError("The release tag moved unexpectedly; publication stopped.")
        return ref["object"]["sha"]

    files = []
    for name in ASSET_NAMES:
        path = root / "dist" / name
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"The tested release artifact is missing or empty: {name}")
        data = path.read_bytes()
        files.append((name, data, hashlib.sha256(data).hexdigest()))

    # The workflow/source must already be on main; a release branch is only the
    # deliberate publication trigger, not a route to release unmerged code.
    for branch in ("main", "release/v0.1.0"):
        ref = request(f"{api_base}/git/ref/heads/{branch}")
        if ref["object"]["sha"] != sha:
            raise RuntimeError(f"{branch} changed during this build; publication stopped.")
    release_guard(set())
    current = tag_guard({INITIAL_SHA, sha})
    if current == INITIAL_SHA:
        # A real Git lease atomically rejects another writer's tag movement.
        # checkout supplies the workflow token's Git credentials; no token is
        # included in this command line or printed in the logs.
        subprocess.run([
            "git", "push", f"--force-with-lease=refs/tags/{TAG}:{INITIAL_SHA}",
            "origin", f"{sha}:refs/tags/{TAG}",
        ], cwd=root, check=True)
    tag_guard({sha})

    uploaded: set[int] = set()
    for name, data, digest in files:
        release_guard(uploaded)
        tag_guard({sha})
        content_type = "application/zip" if name.endswith(".zip") else "application/octet-stream"
        asset = request(
            f"https://uploads.github.com/repos/{REPOSITORY}/releases/{RELEASE_ID}/assets?name={name}",
            data, content_type,
        )
        if asset["name"] != name or asset["state"] != "uploaded" or asset["size"] != len(data):
            raise RuntimeError(f"GitHub did not confirm a complete upload of {name}.")
        if asset.get("digest") and asset["digest"] != "sha256:" + digest:
            raise RuntimeError(f"GitHub's digest differs from the tested artifact: {name}")
        uploaded.add(asset["id"])
        print(f"Uploaded {name}: {len(data)} bytes, SHA-256 {digest}")
    release_guard(uploaded)
    tag_guard({sha})
    print(f"Completed https://github.com/{REPOSITORY}/releases/tag/{TAG} at {sha}; release text preserved.")


if __name__ == "__main__":
    main()

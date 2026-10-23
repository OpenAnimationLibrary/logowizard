"""Exercise the built app outside the checkout, using isolated writable data."""

import argparse
import base64
import csv
import json
import os
import socket
import struct
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


def png_size(data: bytes) -> tuple[int, int]:
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise AssertionError("The app did not return a PNG image.")
    return struct.unpack(">II", data[16:24])


def smoke(executable: Path) -> None:
    executable = executable.resolve(strict=True)
    manifest = executable.parent / "_internal" / "data" / "fonts" / "manifest.csv"
    with manifest.open(newline="", encoding="utf-8") as source:
        expected_fonts = len(list(csv.DictReader(source)))
    for notice in ("LICENSE", "DATA_LICENSES.md", "CREDITS.md"):
        if not (executable.parent / notice).is_file():
            raise AssertionError(f"The distribution is missing {notice}.")

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def request(path: str, payload: dict | None = None) -> tuple[bytes, str]:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(base + path, data=body, headers={"Content-Type": "application/json"})
        with opener.open(req, timeout=30) as response:
            return response.read(), response.headers.get_content_type()

    def request_json(path: str, payload: dict | None = None) -> dict:
        data, content_type = request(path, payload)
        if content_type != "application/json":
            raise AssertionError(f"Unexpected content type for {path}: {content_type}")
        return json.loads(data)

    with tempfile.TemporaryDirectory(prefix="logowizard-smoke-") as folder:
        work = Path(folder)
        home = work / "user-data"
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment.pop("PYTHONHOME", None)
        environment["LOGO_WIZARD_HOME"] = str(home)
        log_path = work / "app.log"
        process = None
        with log_path.open("wb") as log:
            try:
                process = subprocess.Popen(
                    [str(executable), "--no-browser", "--port", str(port)],
                    cwd=work,
                    env=environment,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
                deadline = time.monotonic() + 120
                while True:
                    if process.poll() is not None:
                        raise AssertionError(f"The packaged app exited with {process.returncode}.")
                    try:
                        status = request_json("/api/status")
                        break
                    except (urllib.error.URLError, TimeoutError):
                        if time.monotonic() >= deadline:
                            raise AssertionError("The packaged app did not become ready within 120 seconds.")
                        time.sleep(0.25)
                if status["fonts"] != expected_fonts or expected_fonts == 0:
                    raise AssertionError(f"Expected {expected_fonts} bundled font faces, got {status['fonts']}.")
                if status["layout"] is not None or status["stylizer"] is not None:
                    raise AssertionError("The clean smoke-test home unexpectedly loaded trained models.")
                html, content_type = request("/")
                if content_type != "text/html" or b"Logo Wizard" not in html:
                    raise AssertionError("The bundled user interface did not load.")
                options = request_json("/api/options")
                if len(options["fonts"]) != expected_fonts or not options["palettes"]:
                    raise AssertionError("The bundled font/palette options are incomplete.")
                generated = request_json("/api/generate", {
                    "text": "The Iron Comet", "count": 2, "source": "rules", "seed": 23,
                })
                candidates = generated["candidates"]
                if len(candidates) != 2 or any(item["source"] != "rules" for item in candidates):
                    raise AssertionError("Procedural generation did not return two candidates.")
                for item in candidates:
                    if png_size(base64.b64decode(item["png"], validate=True)) != (512, 320):
                        raise AssertionError("A generated preview has the wrong dimensions.")
                spec = candidates[0]["spec"]
                exported, content_type = request("/api/render", {
                    "spec": spec, "width": 1024, "height": 640, "stylize": False,
                })
                if content_type != "image/png" or png_size(exported) != (1024, 640):
                    raise AssertionError("PNG export returned the wrong type or dimensions.")
                result = request_json("/api/feedback", {"spec": spec, "vote": 1, "source": "rules"})
                if not result.get("ok"):
                    raise AssertionError("Feedback was rejected.")
                feedback = home / "feedback" / "feedback.jsonl"
                rows = [json.loads(line) for line in feedback.read_text(encoding="utf-8").splitlines()]
                if len(rows) != 1 or rows[0]["vote"] != 1 or rows[0]["spec"]["text"] != "The Iron Comet":
                    raise AssertionError("Feedback was not saved in the isolated user-data directory.")
                print(f"Packaged app passed UI, {expected_fonts}-font status/options, generation, PNG export and feedback checks.")
            finally:
                if process is not None and process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=10)
                log.flush()
                print(log_path.read_text(encoding="utf-8", errors="replace"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    smoke(parser.parse_args().executable)

#!/usr/bin/env python3
"""Run the unchanged application's offline checks from any working directory."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import runpy
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
ARTIFACTS = ROOT / ".artifacts"


def offline_child(kind: str) -> None:
    # The tests mock HTTP/COM. Fail if a future check accidentally tries a real
    # Python socket connection or DNS lookup. This is not an OS sandbox.
    def deny_network(event: str, args: tuple) -> None:
        if event in {"socket.connect", "socket.getaddrinfo", "socket.sendto"}:
            raise RuntimeError("Network access is disabled during offline verification")

    sys.addaudithook(deny_network)
    sys.path.insert(0, str(APP))
    if kind == "tests":
        sys.argv = ["unittest", "discover", "-s", ".", "-p", "test_*.py", "-v"]
        runpy.run_module("unittest", run_name="__main__")
    else:
        sys.argv = [str(APP / "desktop_app.py"), "--self-test", "--report",
                    str(ARTIFACTS / "desktop-self-test.json")]
        runpy.run_path(str(APP / "desktop_app.py"), run_name="__main__")


def run_check(kind: str) -> dict:
    command = [sys.executable, "-E", "-s", "-B", str(Path(__file__).resolve()), "--_child", kind]
    started = time.monotonic()
    try:
        result = subprocess.run(command, cwd=APP, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=180)
        output = result.stdout + result.stderr
        code = result.returncode
    except subprocess.TimeoutExpired as exc:
        def decode(value):
            return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else (value or "")
        output = decode(exc.stdout) + decode(exc.stderr) + "\nVerification timed out after 180 seconds.\n"
        code = 124
    (ARTIFACTS / f"{kind}.log").write_text(output, encoding="utf-8")
    check = {"command": command, "cwd": str(APP), "returncode": code,
             "elapsed_seconds": round(time.monotonic() - started, 3)}
    if kind == "tests":
        match = re.search(r"^Ran (\d+) tests? in ", output, re.MULTILINE)
        check["tests_run"] = int(match.group(1)) if match else 0
        check["passed"] = code == 0 and check["tests_run"] > 0
    else:
        try:
            report = json.loads((ARTIFACTS / "desktop-self-test.json").read_text(encoding="utf-8"))
            check["passed"] = code == 0 and report.get("status") == "passed"
        except (OSError, ValueError):
            check["passed"] = False
    print(f"{kind}: {'PASS' if check['passed'] else 'FAIL'}"
          + (f" ({check['tests_run']} tests)" if kind == "tests" else ""))
    if not check["passed"]:
        print(output[-12000:])
    return check


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--_child", choices=("tests", "desktop"), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        parser.error("Python 3.10 or newer is required; Python 3.12 is recommended")
    if args._child:
        offline_child(args._child)
        return 0
    ARTIFACTS.mkdir(exist_ok=True)
    (ARTIFACTS / "desktop-self-test.json").unlink(missing_ok=True)
    checks = {kind: run_check(kind) for kind in ("tests", "desktop")}
    passed = all(check["passed"] for check in checks.values())
    summary = {"status": "passed" if passed else "failed",
               "generated_at_utc": datetime.now(timezone.utc).isoformat(),
               "python": sys.version, "executable": sys.executable, "platform": sys.platform,
               "checks": checks, "python_socket_network_blocked": True,
               "gui_opened": False, "windows_runtime_validated": False,
               "live_jev_api_tested": False, "live_profit_excel_tested": False,
               "order_execution_tested": False}
    (ARTIFACTS / "verification.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Evidence: {ARTIFACTS}")
    if not passed:
        print("If Tk import fails, install Python's Tcl/Tk bindings; these checks do not need a display.")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

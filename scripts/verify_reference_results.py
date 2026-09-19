"""Check a complete v0.3.0 run against the archived reference hashes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True, help="Complete run directory")
    parser.add_argument(
        "--expected",
        type=Path,
        default=Path("config/expected_results_v0.3.0.json"),
    )
    args = parser.parse_args()
    expected = json.loads(args.expected.read_text(encoding="utf-8"))
    failures: list[str] = []
    checked: dict[str, str] = {}
    for relative, wanted in expected["sha256"].items():
        path = args.run / relative
        if not path.is_file():
            failures.append(f"missing: {relative}")
            continue
        actual = sha256(path)
        checked[relative] = actual
        if actual != wanted:
            failures.append(f"hash mismatch: {relative}\n  expected {wanted}\n  actual   {actual}")
    report = {
        "release": expected["release"],
        "files_checked": len(checked),
        "passed": not failures,
        "failures": failures,
    }
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

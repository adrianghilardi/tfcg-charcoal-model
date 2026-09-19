"""Check the five local input rasters against the manifest and grid rules."""

from pathlib import Path
import argparse
import hashlib
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tfcg_charcoal.landscape import INPUT_FILES, prepare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    args = parser.parse_args()
    source = args.source.resolve()
    manifest = json.loads((source / "bundle_manifest.json").read_text(encoding="utf-8"))
    expected = set(INPUT_FILES.values())
    listed = {item["path"] for item in manifest["files"]}
    actual = {path.relative_to(source).as_posix() for path in (source / "InRaster").glob("*.tif")}
    if listed != expected or actual != expected:
        raise ValueError(f"Expected exactly the five configured rasters; listed={listed}, actual={actual}")
    for item in manifest["files"]:
        path = source / item["path"]
        if path.stat().st_size != item["bytes"]:
            raise ValueError(f"Unexpected size: {path}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"Checksum mismatch: {path}")
    _, metadata = prepare(source)
    print(
        f"PASS: {len(expected)} inputs; {metadata['reporting_cells']} reporting cells; "
        f"{metadata['reporting_area_ha']:.3f} ha"
    )


if __name__ == "__main__":
    main()

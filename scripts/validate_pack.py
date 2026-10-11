#!/usr/bin/env python3
"""Validate four-image packs, transparency, dimensions and compositing quality."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image

KINDS = ("full", "clean", "foreground", "background")
PATTERN = re.compile(r"^(S\d{3})_(full|clean|foreground|background)\.png$", re.IGNORECASE)


def open_rgba(path: Path) -> tuple[Image.Image, str]:
    with Image.open(path) as image:
        native_mode = image.mode
        return image.convert("RGBA"), native_mode


def validate_slide(directory: Path, slide_id: str, max_mae: float, ratio: float, min_transparent: float):
    files = {kind: directory / f"{slide_id}_{kind}.png" for kind in KINDS}
    missing = [kind for kind, path in files.items() if not path.is_file()]
    report = {"slide_id": slide_id, "files": {k: str(v.name) for k, v in files.items()}, "errors": [], "warnings": []}
    if missing:
        report["errors"].append(f"Missing required images: {', '.join(missing)}")
        report["passed"] = False
        return report

    images = {}
    modes = {}
    for kind, path in files.items():
        images[kind], modes[kind] = open_rgba(path)
    dimensions = {kind: images[kind].size for kind in KINDS}
    report["dimensions"] = dimensions
    report["native_modes"] = modes
    if len(set(dimensions.values())) != 1:
        report["errors"].append("Mismatched pixel dimensions; all four images must share the same canvas")
        report["passed"] = False
        return report

    w, h = dimensions["full"]
    if h <= 0 or abs(w / h - ratio) > 0.025:
        report["warnings"].append(f"Aspect ratio {w}/{h} differs from nominal {ratio:.6f}")
    fore = images["foreground"]
    fg_alpha = np.asarray(fore.getchannel("A"), dtype=np.uint8)
    transparent_fraction = float(np.mean(fg_alpha < 5))
    foreground_coverage = float(np.mean(fg_alpha > 13))
    report["transparent_fraction_alpha_lt_5"] = round(transparent_fraction, 6)
    report["foreground_coverage_alpha_gt_13"] = round(foreground_coverage, 6)
    if modes["foreground"] != "RGBA":
        report["errors"].append("Foreground PNG must be stored as RGBA, not RGB/palette/fake checkerboard")
    if transparent_fraction < min_transparent:
        report["errors"].append(f"Insufficient transparent area in foreground ({transparent_fraction:.4%}); possible white/opaque background")
    if foreground_coverage > 0.90:
        report["warnings"].append("Foreground covers >90% of canvas; possible retained background")

    for kind in ("full", "clean", "background"):
        a = np.asarray(images[kind].getchannel("A"), dtype=np.uint8)
        if np.min(a) != 255:
            report["errors"].append(f"{kind} contains transparent pixels; expected a fully opaque slide")
    recomposed = Image.alpha_composite(images["background"], fore).convert("RGB")
    clean = np.asarray(images["clean"].convert("RGB"), dtype=np.int16)
    compounded = np.asarray(recomposed, dtype=np.int16)
    err = np.abs(clean - compounded)
    report["recompose_mae_rgb_0_to_255"] = round(float(np.mean(err)), 6)
    report["recompose_p95_abs_error_rgb"] = float(np.percentile(err, 95))
    report["recompose_max_abs_error_rgb"] = int(np.max(err))
    if report["recompose_mae_rgb_0_to_255"] > max_mae:
        report["errors"].append(f"Composite MAE {report['recompose_mae_rgb_0_to_255']} exceeds {max_mae}")
    full = np.asarray(images["full"].convert("RGB"), dtype=np.int16)
    full_to_clean_change = float(np.mean(np.max(np.abs(full - clean), axis=2) > 10))
    report["full_vs_clean_changed_pixel_fraction_gt_10"] = round(full_to_clean_change, 6)
    if full_to_clean_change > 0.55:
        report["warnings"].append("Full and clean images differ over >55% of canvas. Check for non-text changes.")
    report["manual_checks_required"] = [
        "clean contains no text and retains identical non-text design",
        "background contains no foreground objects or text",
        "foreground contains no text, checkerboard, unwanted backdrop or hard halos",
        "background texture is continuous under removed elements",
    ]
    report["passed"] = not report["errors"]
    return report


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True, help="Folder holding S001_* files")
    p.add_argument("--max-mae", type=float, default=1.5)
    p.add_argument("--min-transparent", type=float, default=0.01)
    p.add_argument("--aspect-ratio", type=float, default=16 / 9)
    p.add_argument("--report", type=Path, help="Defaults to <input>/QA_REPORT.json")
    args = p.parse_args()
    if not args.input.is_dir():
        p.error(f"Not a directory: {args.input}")
    ids = {m.group(1).upper() for file in args.input.glob("S*.png") if (m := PATTERN.match(file.name))}
    report_path = args.report or args.input / "QA_REPORT.json"
    result = {"skill": "ppt-layered-image-pack", "slides": [], "all_passed": False}
    if not ids:
        result["error"] = "No S###_{full,clean,foreground,background}.png files found"
        report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(result["error"])
        return 2
    ordered = sorted(ids)
    actual_numbers = [int(x[1:]) for x in ordered]
    if actual_numbers != list(range(1, len(actual_numbers) + 1)):
        result["warning"] = "Slide IDs are not consecutive from S001"
    for slide_id in ordered:
        result["slides"].append(validate_slide(args.input, slide_id, args.max_mae, args.aspect_ratio, args.min_transparent))
    result["all_passed"] = all(s["passed"] for s in result["slides"])
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for s in result["slides"]:
        status = "PASS" if s["passed"] else "FAIL"
        print(f"{s['slide_id']}: {status}, MAE={s.get('recompose_mae_rgb_0_to_255', 'N/A')}, errors={s['errors']}")
        for warning in s["warnings"]:
            print(f"  Warning: {warning}")
    print(f"Report: {report_path}")
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

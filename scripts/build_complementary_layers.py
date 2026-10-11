#!/usr/bin/env python3
"""Derive a compositable RGBA foreground from a clean slide and background.

Dependencies: Pillow, NumPy. This is a color/alpha recovery utility, not a
semantic segmenter. Provide a well-aligned foreground mask for good isolation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


def read_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        if im.mode in ("RGBA", "LA") or "transparency" in im.info:
            rgba = im.convert("RGBA")
            a = np.asarray(rgba.getchannel("A"), dtype=np.uint8)
            if np.min(a) != 255:
                raise ValueError(f"{path}: input clean/background must be opaque, not transparent")
        return np.asarray(im.convert("RGB"), dtype=np.float32)


def read_mask(mask_path: Path, target_size: tuple[int, int]) -> np.ndarray:
    with Image.open(mask_path) as im:
        if im.size != target_size:
            raise ValueError(f"Mask {im.size} does not match target size {target_size}")
        if "A" in im.getbands() and im.getchannel("A").getextrema() != (255, 255):
            gray = im.getchannel("A")
        else:
            gray = im.convert("L")
        return np.asarray(gray, dtype=np.float32) / 255.0


def estimate_mask(clean: np.ndarray, background: np.ndarray) -> np.ndarray:
    # A convenient fallback, not a replacement for semantic masking.
    residual = np.max(np.abs(clean - background), axis=2)
    mask = np.clip((residual - 3.0) / 21.0, 0.0, 1.0)
    im = Image.fromarray(np.uint8(np.rint(mask * 255)), mode="L")
    im = im.filter(ImageFilter.GaussianBlur(radius=0.8))
    return np.asarray(im, dtype=np.float32) / 255.0


def alpha_required(clean: np.ndarray, background: np.ndarray) -> np.ndarray:
    """Find the minimum physically feasible opacity for each RGB target pixel."""
    increasing = np.maximum(clean - background, 0.0)
    decreasing = np.maximum(background - clean, 0.0)
    higher = np.divide(
        increasing, 255.0 - background,
        out=np.zeros_like(increasing), where=(255.0 - background) > 0,
    )
    lower = np.divide(
        decreasing, background,
        out=np.zeros_like(decreasing), where=background > 0,
    )
    return np.clip(np.maximum(higher, lower).max(axis=2), 0.0, 1.0)


def derive_foreground(clean: np.ndarray, background: np.ndarray, mask: np.ndarray):
    min_alpha = alpha_required(clean, background)
    alpha = np.maximum(mask, min_alpha)
    den = alpha[..., None]
    numerator = clean - (1.0 - den) * background
    color = np.divide(numerator, den, out=np.zeros_like(clean), where=den > 1e-8)
    color = np.rint(np.clip(color, 0.0, 255.0)).astype(np.uint8)
    alpha_byte = np.rint(alpha * 255.0).astype(np.uint8)
    rgba = np.dstack((color, alpha_byte))
    return rgba, alpha, min_alpha


def recompose(background: np.ndarray, foreground: np.ndarray) -> np.ndarray:
    bg_im = Image.fromarray(background.astype(np.uint8), mode="RGB").convert("RGBA")
    fg_im = Image.fromarray(foreground, mode="RGBA")
    return np.asarray(Image.alpha_composite(bg_im, fg_im).convert("RGB"), dtype=np.uint8)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--clean", type=Path, required=True)
    p.add_argument("--background", type=Path, required=True)
    p.add_argument("--mask", type=Path, help="Optional grayscale mask or RGBA image with true alpha")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--report", type=Path, help="JSON diagnostic path; defaults to <out stem>_layer_report.json")
    p.add_argument("--preview", type=Path, help="Optional recomposited RGB PNG for visual QC")
    args = p.parse_args()

    clean = read_rgb(args.clean)
    bg = read_rgb(args.background)
    if clean.shape != bg.shape:
        p.error(f"clean and background must match dimensions: {clean.shape} vs {bg.shape}")

    h, w = clean.shape[:2]
    has_manual_mask = args.mask is not None
    mask = read_mask(args.mask, (w, h)) if has_manual_mask else estimate_mask(clean, bg)
    foreground, alpha, min_alpha = derive_foreground(clean, bg, mask)
    preview = recompose(bg, foreground)
    absolute_error = np.abs(preview.astype(np.float32) - clean)
    mae = float(np.mean(absolute_error))
    max_err = int(np.max(absolute_error))

    strong_outside = float(np.mean((mask < 0.05) & (min_alpha > 0.05)))
    visible_foreground = float(np.mean(alpha > 0.05))
    transparent_fraction = float(np.mean(foreground[..., 3] == 0))
    result = {
        "clean": str(args.clean),
        "background": str(args.background),
        "mask": str(args.mask) if has_manual_mask else None,
        "mask_provenance": "provided" if has_manual_mask else "heuristic-difference",
        "foreground": str(args.out),
        "dimensions": [w, h],
        "composite_mae_rgb_0_to_255": round(mae, 6),
        "composite_max_abs_error_rgb": max_err,
        "foreground_coverage_alpha_gt_0_05": round(visible_foreground, 6),
        "fully_transparent_fraction": round(transparent_fraction, 6),
        "required_alpha_outside_supplied_mask_fraction": round(strong_outside, 6) if has_manual_mask else None,
        "warnings": [],
    }
    if not has_manual_mask:
        result["warnings"].append("Estimated a mask from pixel differences. Verify visual isolation and halo edges manually.")
    if visible_foreground > 0.88:
        result["warnings"].append("Most of the slide is assigned to the foreground. Check background drift/leakage.")
    if has_manual_mask and strong_outside > 0.01:
        result["warnings"].append("Strong clean/background differences outside the supplied mask: possible background-edit drift or incomplete mask.")
    if mae > 1.5:
        result["warnings"].append("Recomposition MAE exceeds the suggested 1.5/255 threshold.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(foreground, mode="RGBA").save(args.out, format="PNG", optimize=True)
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(preview, mode="RGB").save(args.preview, format="PNG")
    report_path = args.report or args.out.with_name(args.out.stem + "_layer_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

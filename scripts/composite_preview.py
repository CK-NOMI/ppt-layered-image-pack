#!/usr/bin/env python3
"""Composite a transparent PPT foreground over its matching background."""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--background", type=Path, required=True)
    parser.add_argument("--foreground", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with Image.open(args.background) as bg_im, Image.open(args.foreground) as fg_im:
        if bg_im.size != fg_im.size:
            parser.error(f"Misaligned dimensions: {bg_im.size} versus {fg_im.size}")
        if fg_im.mode != "RGBA":
            parser.error("Foreground must have a real RGBA channel")
        output = Image.alpha_composite(bg_im.convert("RGBA"), fg_im).convert("RGB")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        output.save(args.out, format="PNG")
        print(f"Saved: {args.out}")


if __name__ == "__main__":
    main()

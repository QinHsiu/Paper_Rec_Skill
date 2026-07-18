"""CLI: python -m lib … from skill-draw directory, or python lib/cli.py"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Paper_Rec /draw — self-contained charts")
    p.add_argument("--data", required=True)
    p.add_argument("--desc", required=True)
    p.add_argument("--chart", default="")
    p.add_argument("--out", required=True, help="output stem without extension")
    p.add_argument("--format", default="pdf,png")
    p.add_argument("--xlabel", default="")
    p.add_argument("--ylabel", default="")
    p.add_argument("--title", default="")
    args = p.parse_args(argv)

    # allow `python -m lib.cli` with package root = skill-draw
    import sys

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from lib.draw import draw

    result = draw(
        args.data,
        args.desc,
        chart=args.chart or None,
        out_stem=args.out,
        formats=tuple(x.strip() for x in args.format.split(",") if x.strip()),
        xlabel=args.xlabel,
        ylabel=args.ylabel,
        title=args.title,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

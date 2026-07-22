"""Assemble a silent promo MP4/GIF slideshow from docs/promo/shots."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "shots"
OUT = ROOT / "out"
OUT.mkdir(parents=True, exist_ok=True)

ORDER = [
    ("01-home.png", 2.5),
    ("02-pages.png", 2.5),
    ("03-read-dual.png", 3.2),
    ("04-thread.png", 3.0),
    ("05-experiments.png", 2.4),
    ("06-ask.png", 2.4),
    ("07-skills.png", 2.0),
    ("07-endcard.png", 3.0),
]


def main() -> int:
    frames = []
    for name, sec in ORDER:
        p = SHOTS / name
        if p.exists():
            frames.append((p, sec))
        else:
            print(f"skip missing {name}")
    if not frames:
        print("no frames", file=sys.stderr)
        return 1

    # Prefer ffmpeg if present
    list_file = OUT / "concat.txt"
    # Build stills as short clips via image2pipe is hard on Windows; use filter_complex or concat demuxer with loop.
    # Simpler: Pillow + imageio if available.
    try:
        from PIL import Image
        import imageio.v2 as imageio
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow", "imageio", "imageio-ffmpeg", "-q"])
        from PIL import Image
        import imageio.v2 as imageio

    target = (1280, 720)
    writer_path = OUT / "paper-rec-grad-demo.mp4"
    fps = 2
    images = []
    for path, sec in frames:
        im = Image.open(path).convert("RGB")
        im.thumbnail(target, Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", target, (18, 28, 26))
        x = (target[0] - im.size[0]) // 2
        y = (target[1] - im.size[1]) // 2
        canvas.paste(im, (x, y))
        n = max(1, int(sec * fps))
        for _ in range(n):
            images.append(canvas.copy())

    imageio.mimsave(writer_path, images, fps=fps, codec="libx264", quality=8)
    print(f"wrote {writer_path} ({len(images)} frames @ {fps}fps)")

    # Also GIF for chat preview
    gif_path = OUT / "paper-rec-grad-demo.gif"
    gif_frames = images[::2]  # lighter
    imageio.mimsave(gif_path, gif_frames, fps=1, loop=0)
    print(f"wrote {gif_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

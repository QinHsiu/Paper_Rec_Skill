"""Higher-quality promo narration.

Default: Microsoft Edge neural TTS (zh-CN-XiaoxiaoNeural) with per-cue
prosody + ffmpeg timeline (smoother than single-pass Yunyang).

Optional engines (need your own key in the environment — never printed):
  --engine openai   -> OpenAI tts-1-hd / gpt-4o-mini-tts
  --engine edge     -> Edge Xiaoxiao (default)

  python docs/promo/add_narration.py
  python docs/promo/add_narration.py --engine openai --voice nova
"""
from __future__ import annotations

import argparse
import asyncio
import os
import re
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "shots"
OUT = ROOT / "out"
SRT = OUT / "narration.zh.srt"
ORDER = [
    "01-home.png",
    "02-pages.png",
    "03-read-dual.png",
    "04-thread.png",
    "05-experiments.png",
    "06-ask.png",
    "07-skills.png",
    "07-endcard.png",
]

# Narrative female — usually smoother for product demos than Yunyang
EDGE_VOICE = "zh-CN-XiaoxiaoNeural"
EDGE_RATE = "-8%"
EDGE_PITCH = "+0Hz"


def ffmpeg_exe() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def parse_srt(path: Path) -> list[tuple[float, float, str]]:
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"\n\s*\n", text.strip())
    cues: list[tuple[float, float, str]] = []
    for block in blocks:
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if len(lines) < 2:
            continue
        if re.fullmatch(r"\d+", lines[0]):
            lines = lines[1:]
        if "-->" not in lines[0]:
            continue
        a, b = [x.strip() for x in lines[0].split("-->")]
        cues.append((_ts(a), _ts(b), " ".join(lines[1:])))
    return cues


def _ts(s: str) -> float:
    s = s.replace(",", ".")
    h, m, rest = s.split(":")
    return int(h) * 3600 + int(m) * 60 + float(rest)


def write_silence_wav(path: Path, seconds: float, rate: int = 24000) -> None:
    n = max(0, int(seconds * rate))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * n)


def to_wav(src: Path, dst: Path, rate: int = 24000) -> None:
    ff = ffmpeg_exe()
    cmd = [
        ff,
        "-y",
        "-i",
        str(src),
        "-ac",
        "1",
        "-ar",
        str(rate),
        "-sample_fmt",
        "s16",
        str(dst),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-1500:])


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def concat_wavs(parts: list[Path], out: Path) -> float:
    """Simple PCM concat (all same format)."""
    frames = []
    rate = None
    for p in parts:
        with wave.open(str(p), "rb") as w:
            if rate is None:
                rate = w.getframerate()
                params = w.getparams()
            elif w.getframerate() != rate or w.getnchannels() != params.nchannels:
                raise RuntimeError(f"format mismatch: {p}")
            frames.append(w.readframes(w.getnframes()))
    assert rate is not None
    with wave.open(str(out), "wb") as w:
        w.setparams(params)
        for fr in frames:
            w.writeframes(fr)
    return wav_duration(out)


async def edge_cue_mp3(text: str, out: Path, voice: str) -> None:
    import edge_tts

    await edge_tts.Communicate(
        text,
        voice,
        rate=EDGE_RATE,
        pitch=EDGE_PITCH,
    ).save(str(out))


async def synth_edge(cues: list[tuple[float, float, str]], work: Path, voice: str) -> Path:
    """One continuous take (no SRT timeline gaps). Fallback: stitch cues with short breaths."""
    work.mkdir(parents=True, exist_ok=True)
    # Prefer single utterance — no mid-track silence from slot padding
    full = "".join(t if t.endswith(("。", "！", "？", ".", "!", "?")) else t + "。" for _, _, t in cues)
    mp3 = work / "full.mp3"
    wav = work / "full.wav"
    print(f"edge continuous ({len(full)} chars)…")
    try:
        await edge_cue_mp3(full, mp3, voice)
        to_wav(mp3, wav)
        narr_wav = wav
    except Exception as e:
        print(f"single-pass failed ({e}); stitching cues…")
        timeline_parts: list[Path] = []
        breath = work / "breath.wav"
        write_silence_wav(breath, 0.28)
        for i, (_start, _end, text) in enumerate(cues):
            c_mp3 = work / f"cue_{i:02d}.mp3"
            c_wav = work / f"cue_{i:02d}.wav"
            await edge_cue_mp3(text, c_mp3, voice)
            to_wav(c_mp3, c_wav)
            timeline_parts.append(c_wav)
            if i < len(cues) - 1:
                timeline_parts.append(breath)
        tail = work / "sil_tail.wav"
        write_silence_wav(tail, 0.4)
        timeline_parts.append(tail)
        narr_wav = work / "narration.wav"
        concat_wavs(timeline_parts, narr_wav)

    total = wav_duration(narr_wav)
    narr_mp3 = OUT / "narration.zh.mp3"
    ff = ffmpeg_exe()
    subprocess.run(
        [ff, "-y", "-i", str(narr_wav), "-codec:a", "libmp3lame", "-q:a", "2", str(narr_mp3)],
        check=True,
        capture_output=True,
    )
    print(f"narration -> {narr_mp3} ({total:.1f}s continuous)")
    return narr_mp3


async def synth_openai(cues: list[tuple[float, float, str]], voice: str) -> Path:
    """Requires OPENAI_API_KEY. Uses tts-1-hd for clarity."""
    try:
        from openai import OpenAI
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openai", "-q"])
        from openai import OpenAI

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY not set — export it then re-run with --engine openai")

    client = OpenAI()
    work = OUT / "_tts_work"
    work.mkdir(parents=True, exist_ok=True)
    script = "".join(t if t.endswith(("。", "！", "？")) else t + "。" for _, _, t in cues)
    model = os.environ.get("OPENAI_TTS_MODEL", "tts-1-hd")
    print(f"openai tts model={model} voice={voice}")
    speech = client.audio.speech.create(
        model=model,
        voice=voice,
        input=script,
        speed=0.95,
    )
    raw = work / "openai.bin"
    raw.write_bytes(speech.content)
    narr = OUT / "narration.zh.mp3"
    ff = ffmpeg_exe()
    r = subprocess.run(
        [ff, "-y", "-i", str(raw), "-codec:a", "libmp3lame", "-q:a", "2", str(narr)],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        narr.write_bytes(raw.read_bytes())
    print(f"narration -> {narr}")
    return narr


def audio_duration_ff(path: Path) -> float:
    ff = ffmpeg_exe()
    r = subprocess.run([ff, "-i", str(path)], capture_output=True, text=True)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", r.stderr or "")
    if not m:
        return 82.0
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def build_silent_video(duration: float, out_path: Path) -> Path:
    from PIL import Image
    import imageio.v2 as imageio

    fps = 2
    target = (1280, 720)
    n = max(fps, int(round(duration * fps)))
    paths = [SHOTS / name for name in ORDER if (SHOTS / name).exists()]
    frames = []
    per = max(1, n // len(paths))
    for i, path in enumerate(paths):
        im = Image.open(path).convert("RGB")
        im.thumbnail(target, Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", target, (18, 28, 26))
        canvas.paste(im, ((target[0] - im.size[0]) // 2, (target[1] - im.size[1]) // 2))
        count = per if i < len(paths) - 1 else max(1, n - per * (len(paths) - 1))
        frames.extend([canvas.copy()] * count)
    imageio.mimsave(out_path, frames, fps=fps, codec="libx264", quality=8)
    return out_path


def mux(video: Path, audio: Path, out: Path) -> None:
    ff = ffmpeg_exe()
    cmd = [
        ff,
        "-y",
        "-i",
        str(video),
        "-i",
        str(audio),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(out),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2000:], file=sys.stderr)
        raise SystemExit(r.returncode)


async def amain() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=("edge", "openai"), default="edge")
    ap.add_argument(
        "--voice",
        default="",
        help="edge: zh-CN-XiaoxiaoNeural|XiaoyiNeural|YunxiNeural; openai: nova|shimmer|alloy|…",
    )
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    cues = parse_srt(SRT)
    work = OUT / "_tts_work"
    work.mkdir(parents=True, exist_ok=True)

    if args.engine == "openai":
        voice = args.voice or "nova"
        narr = await synth_openai(cues, voice)
    else:
        voice = args.voice or EDGE_VOICE
        narr = await synth_edge(cues, work, voice)

    dur = audio_duration_ff(narr)
    print(f"audio ≈ {dur:.1f}s")
    silent = OUT / "_silent.mp4"
    build_silent_video(dur + 0.4, silent)
    tmp = OUT / "_with_audio.mp4"
    mux(silent, narr, tmp)
    silent.unlink(missing_ok=True)
    final = OUT / "paper-rec-grad-demo.mp4"
    if final.exists():
        final.unlink()
    tmp.rename(final)
    print(f"done -> {final}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(amain()))

#!/usr/bin/env python3
import argparse
from pathlib import Path

import librosa
import soundfile as sf


def parse_time(s: str) -> float:
    parts = s.split(':')
    if len(parts) == 3:
        h, m, sec = map(float, parts)
        return h * 3600 + m * 60 + sec
    if len(parts) == 2:
        m, sec = map(float, parts)
        return m * 60 + sec
    return float(s)


def write_wav(path: Path, audio, sr: int):
    sf.write(str(path), audio, sr, format='MP3')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='截取音频并输出 wav')
    parser.add_argument('input')
    parser.add_argument('-o', '--output')
    parser.add_argument('--start', default='0:06')
    parser.add_argument('--end', default='28:10')
    args = parser.parse_args()

    inp = Path(args.input)
    out = Path(args.output) if args.output else inp.with_name(f'{inp.stem}_clip.mp3')

    audio, sr = librosa.load(inp, sr=16000, mono=True)
    total = len(audio) / sr
    start_sec, end_sec = parse_time(args.start), parse_time(args.end)
    start, end = int(start_sec * sr), min(int(end_sec * sr), len(audio))

    write_wav(out, audio[start:end], sr)
    actual = (end - start) / sr
    print(f'源 {total/60:.1f}min | 请求 {args.start}~{args.end} | 实际 {actual:.1f}s | {out}')

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COSYVOICE_DIR = ROOT / "cosyvoice"
sys.path.insert(0, str(COSYVOICE_DIR))
sys.path.append(str(COSYVOICE_DIR / "third_party/Matcha-TTS"))

import torch
from cosyvoice.cli.cosyvoice import AutoModel

from core.utils import load_json


DEFAULT_PROMPT_TEXT = "You are a helpful assistant.<|endofprompt|>"


def sanitize_filename(text: str) -> str:
    return re.sub(r'[\\/:*?"<>|：？?]', "", text).strip()


def episode_output_name(episode: dict) -> str:
    ep_id = episode["episode_id"]
    title = sanitize_filename(episode["title"])
    question = sanitize_filename(episode["central_question"].rstrip("？?"))
    return f"{ep_id}_{title}_{question}.mp3"


def ep_number(episode_id: str) -> int:
    match = re.search(r"\d+", episode_id)
    if not match:
        raise ValueError(f"Cannot parse episode number from: {episode_id}")
    return int(match.group())


def load_text_from_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def save_mp3(path: str, audio, sample_rate: int) -> None:
    import torchaudio
    torchaudio.save(path, audio, sample_rate)


def synthesize_episode(cosyvoice, target_text: str, prompt_text: str, prompt_wav: str):
    for result in cosyvoice.inference_zero_shot(
        target_text,
        prompt_text,
        prompt_wav,
        stream=False,
    ):
        return result["tts_speech"]
    return None


def batch_synthesize(
    outline_path: str | Path,
    script_dir: str | Path,
    output_dir: str | Path,
    model_dir: str | Path,
    prompt_wav: str | Path,
    prompt_text: str = DEFAULT_PROMPT_TEXT,
    skip_until_ep: int = 0,
    stop_if_missing: bool = True,
) -> None:
    outline = load_json(outline_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if torch.cuda.is_available():
        print(f"CUDA available: {torch.cuda.get_device_name(0)}")
    else:
        print("CUDA not available, using CPU")

    print(f"Loading model from {model_dir}...")
    cosyvoice = AutoModel(model_dir=str(model_dir))

    for episode in outline["episodes"]:
        ep_id = episode["episode_id"]
        output_path = output_dir / episode_output_name(episode)
        script_path = Path(script_dir) / f"{ep_id}_script_final.txt"

        if ep_number(ep_id) < skip_until_ep:
            print(f"Skip {ep_id}: ep < {skip_until_ep}")
            continue

        if output_path.exists():
            print(f"Skip {ep_id}: output exists")
            continue

        if not script_path.exists():
            msg = f"Script not ready: {script_path}"
            if stop_if_missing:
                print(f"{msg}, stopping batch")
                break
            print(f"{msg}, skipping")
            continue

        print(f"Generating {ep_id} -> {output_path.name}")
        target_text = load_text_from_file(str(script_path))
        print(f"Loaded script ({len(target_text)} chars)")

        audio = synthesize_episode(
            cosyvoice,
            target_text,
            prompt_text,
            str(prompt_wav),
        )
        if audio is None:
            print(f"Failed {ep_id}: no audio generated")
            continue

        save_mp3(str(output_path), audio, cosyvoice.sample_rate)
        print(f"Done: {output_path}")

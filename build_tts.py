"""台本 → mp3: 调用 CosyVoice zero_shot 批量生成"""

from pathlib import Path
from core.config import get_project_config
from audio.synthesize import batch_synthesize

PROJECT = "how_to_use_AI_for_analysis"  # ← 改这里切换项目
PROMPT_WAV = "asset/voice/bon_clean_clip.wav"
PROMPT_TXT = "asset/voice/bon_clean_clip.txt"
SKIP_UNTIL = 0
STOP_IF_MISSING = True


def load_text(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def main():
    cfg = get_project_config(PROJECT)
    prompt_text = "You are a helpful assistant.<|endofprompt|>" + load_text(PROMPT_TXT)
    batch_synthesize(
        outline_path=cfg.outline_path,
        script_dir=cfg.script_dir,
        output_dir=cfg.output_dir,
        model_dir="cosyvoice/pretrained_models/Fun-CosyVoice3-0.5B",
        prompt_wav=PROMPT_WAV,
        prompt_text=prompt_text,
        skip_until_ep=SKIP_UNTIL,
        stop_if_missing=STOP_IF_MISSING,
    )


if __name__ == "__main__":
    main()

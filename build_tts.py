"""台本 → mp3: 调用 CosyVoice zero_shot 批量生成"""

from core.config import get_project_config
from audio.synthesize import batch_synthesize, DEFAULT_PROMPT_TEXT

PROJECT = "neg_explain"  # ← 改这里切换项目
PROMPT_WAV = "asset/voice/bon_clean_clip.wav"
SKIP_UNTIL = 0
STOP_IF_MISSING = True


def main():
    cfg = get_project_config(PROJECT)
    batch_synthesize(
        outline_path=cfg.outline_path,
        script_dir=cfg.script_dir,
        output_dir=cfg.output_dir,
        model_dir="cosyvoice/pretrained_models/Fun-CosyVoice3-0.5B",
        prompt_wav=PROMPT_WAV,
        prompt_text=DEFAULT_PROMPT_TEXT,
        skip_until_ep=SKIP_UNTIL,
        stop_if_missing=STOP_IF_MISSING,
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
最佳实践：zero_shot + 参考音频转写对齐 + 按句分段合成

流程:
  python clip.py bon.mp3 -o prompt.wav --start 3:00 --end 3:10
  python transcribe.py prompt.wav          # → prompt.txt（OpenAI/Groq API，见 transcribe.py 说明）
  python test.py
"""
import sys
from pathlib import Path

import torch
import torchaudio

# ============ 路径配置 ============
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / 'cosyvoice'))
sys.path.append(str(ROOT / 'cosyvoice/third_party/Matcha-TTS'))

ASSET_DIR = ROOT / 'asset'
MODEL_DIR = ROOT / 'cosyvoice' / 'pretrained_models' / 'Fun-CosyVoice3-0.5B'
OUTPUT_DIR = ROOT / 'output'

from cosyvoice.cli.cosyvoice import AutoModel



def main():
    prompt_text = '''
这是一段测试
    '''
    reference_text = 'You are a helpful assistant.<|endofprompt|>内个房子是他爸做枫糖糖浆的一个手工作坊。那个真正小木屋比那个房子要小非常多，只有一个狭窄的空间。然后他自己在那儿生活取暖，然后他父亲每两周来看他一次，给他送食物、水和用品。'
    reference_audio = str(ASSET_DIR / 'curr/bon_clean_clip.wav')
    
    cosyvoice = AutoModel(model_dir=str(MODEL_DIR))
    
    # 用于存储所有生成的音频片段
    audio_segments = []
    sample_rate = None
    
    # zero_shot usage
    for i, j in enumerate(cosyvoice.inference_zero_shot(prompt_text, reference_text,
                                                        reference_audio, stream=False)):
        speech = j['tts_speech']
        audio_segments.append(speech)
        if sample_rate is None:
            sample_rate = cosyvoice.sample_rate
        output_file = ROOT / f'zero_shot_{i}.wav'
        torchaudio.save(str(output_file), speech, sample_rate)
    
    # 拼接所有音频片段
    if audio_segments:
        # 创建0.3秒的停顿
        silence_duration = 0.3
        silence_samples = int(sample_rate * silence_duration)
        silence = torch.zeros(1, silence_samples)
        
        # 在每个片段之间插入停顿
        combined_audio_with_pause = []
        for i, segment in enumerate(audio_segments):
            combined_audio_with_pause.append(segment)
            if i < len(audio_segments) - 1:  # 最后一个片段后不添加停顿
                combined_audio_with_pause.append(silence)
        
        combined_audio = torch.cat(combined_audio_with_pause, dim=-1)
        output_path = OUTPUT_DIR / 'output_combined.wav'
        torchaudio.save(str(output_path), combined_audio, sample_rate)
        print(f'已生成拼接音频：{output_path}')
        
        # 删除中间生成的音频文件
        for i in range(len(audio_segments)):
            file_path = ROOT / f'zero_shot_{i}.wav'
            if file_path.exists():
                file_path.unlink()
                print(f'已删除：{file_path}')

if __name__ == '__main__':
    main()

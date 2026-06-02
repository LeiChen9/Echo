# 系统架构

## 流程

原始音频 → **一次性预处理**（音色资产）→ **CosyVoice 反复合成**

```
mp3 → [AudioProcess] → prompt.wav + prompt.txt → [CosyVoice zero_shot] → output.wav
```

```bash
python clip.py input.mp3 -o prompt.wav --start 3:00 --end 3:10
python transcribe.py prompt.wav   # API 转写 → prompt.txt，需人工校对
python test.py
```

## AudioProcess

切分 · mp3→16kHz wav · 转录 · 人声分离（UVR5）

产出一次性资产，流程可复用；实现不限于代码（API/网页均可）。

| 产出 | 要求 |
|------|------|
| `prompt.wav` | 3~10s，最长 30s，单人干声 wav |
| `prompt.txt` | 与 wav 内容逐字一致 |

转录：OpenAI / Groq Whisper API，或手写 `prompt.txt`。

## CosyVoice

模型 `Fun-CosyVoice3-0.5B`，用 **`inference_zero_shot`**（音色+语气最佳）。

Prompt 前缀固定：`You are a helpful assistant.<|endofprompt|>` + `prompt.txt`

长文本按句分段合成再拼接。仅支持 wav 输入。

| 模式 | 何时用 |
|------|--------|
| zero_shot | 默认，需对齐的 prompt.txt |
| cross_lingual | 无转写时兜底，易机械 |
| instruct2 | 需控语气/方言时 |

## 排错

- 乱码 / 极短输出 → prompt 与音频不一致，或参考音频过长
- 机械卡顿 → 别用 cross_lingual；长文须分段
- mp3 报错 → 先 `clip.py` 转 wav

## 待做

说话人注册 · 人声分离接入 · 服务化

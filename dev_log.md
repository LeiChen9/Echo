# TTS 气口 & 发音问题修复方案

## 背景

- 问题：CosyVoice 合成音频时，气口（呼吸/停顿）不自然，短句碎片化导致韵律丢失；缩写（SQL, Claude 等）发音随机
- 本次目标：通过调整 split_paragraph 参数 + 短句合并逻辑改善气口
- 发音问题待下次讨论

## 改动文件

`cosyvoice/cosyvoice/utils/frontend_utils.py`

## 改动一：增大分句窗口

函数 `split_paragraph` 签名：

```python
# 修改前
def split_paragraph(text, tokenize, lang="zh", token_max_n=80, token_min_n=60, merge_len=20, comma_split=False):

# 修改后
def split_paragraph(text, tokenize, lang="zh", token_max_n=200, token_min_n=120, merge_len=40, comma_split=False):
```

| 参数 | 原值 | 新值 | 说明 |
|------|------|------|------|
| `token_max_n` | 80 | 200 | 每块最大字符数（中文直接计字），越大每句推理上下文越完整 |
| `token_min_n` | 60 | 120 | 低于此不切块，防止过小碎片 |
| `merge_len` | 20 | 40 | 尾部短块合并阈值，同步提升 |

效果：每块从 ~80 字 → ~200 字，分块数减少 60%，跨句韵律更完整。

## 改动二：合并短句

在 `split_paragraph` 的 first-pass split（按标点切分）之后、second-pass merge（按长度合并）之前，插入一段逻辑：

```python
SOFT_PUNC = {'？', '！', '、'}
MIN_UTT_LEN = 15
merged = []
i = 0
while i < len(utts):
    if (utts[i][-1] in SOFT_PUNC and len(utts[i]) < MIN_UTT_LEN
            and i + 1 < len(utts)):
        merged.append(utts[i] + utts[i + 1])
        i += 2
    else:
        merged.append(utts[i])
        i += 1
utts = merged
```

效果：`Agent化是什么？`（7 字）这类短句不会独立成块，而是与后续句子合并，让模型拿到完整上下文做韵律推理。

不写死任何具体词汇，按长度和标点类型判断，换书依然生效。

## 预期效果

1. 每块更大 → 模型有更多上下文 → 句间韵律更自然
2. 短句不独立 → 减少碎片感，气口不突兀

## 部署流程

```bash
cd cosyvoice
# 改完 frontend_utils.py 后
git add cosyvoice/utils/frontend_utils.py
git commit -m "增大分句窗口 token_max_n:80→200; 合并短句"
git push
# 注意：确保 remote 指向自己有写入权限的 fork
```

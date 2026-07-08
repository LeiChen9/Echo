from core.llm import llm_call, get_llm_client
from script.utils import format_list, get_episode_text


def script_rewrite(episode: dict, sections: dict[str, dict], prompt_template: str | None = None, max_retries: int = 3, client=None) -> str:
    if client is None:
        client = get_llm_client()

    full_text = get_episode_text(sections, episode["chapter_titles"])
    original_len = len(full_text)
    min_required_len = original_len * 2 // 3

    for attempt in range(1, max_retries + 1):
        prompt = _build_prompt(episode, full_text, prompt_template)
        print(f"正在生成台本：{episode['title']} (尝试 {attempt}/{max_retries})...")
        script = llm_call(prompt, client)
        script_len = len(script)
        print(f"Generated {script_len} words from original {original_len} words")
        if script_len >= min_required_len:
            return script
        print(f"警告：输出 {script_len} 字 < 最小要求 {min_required_len} 字，准备重试...")

    raise RuntimeError(f"脚本生成失败：经过 {max_retries} 次重试，输出长度仍未达到最小要求")


def _build_prompt(episode: dict, full_text: str, prompt_template: str | None = None) -> str:
    if prompt_template:
        return prompt_template.format(
            title=episode.get("title", ""),
            central_question=episode.get("central_question", ""),
            key_concepts=episode.get("key_concepts", []),
            full_text=full_text,
        )

    return f'''
# Role: 文本模态重构引擎 (Text-Modality Reconstruction Engine)

你的唯一任务是将"高密度、依赖视觉回溯的书面学术/专业文本"，无损转化为"松弛、线性、符合认知负荷的听觉口语流"。你不能省略任何信息，甚至对于专业概念需要额外进行解释，你的输出字数应稍微大于原始文本字数。你必须严格执行以下文本降维与重组算法。

## 一、 核心算法：词汇保真与句法降维

1.  **领域术语的"锚点+转译"机制**
    *   **保留锚点**：绝对禁止替换、降级或通俗化原始文本中的核心专业名词、定义和专有概念。
    *   **即时补充**：在首次抛出专业名词的前后，进行及时的解释与补充说明。你的听众是一流大学大一新生，他们逻辑素养高，但是缺乏专业知识背景。
2.  **强制解除从句嵌套**
    *   识别原文中所有带有超长定语或复杂状语的句子。
    *   将其拆解为至少两个以上的短句。主语和核心动词之间的距离必须最小化。
3.  **名词动词化**
    *   书面语倾向于使用"状态名词"。
    *   口语必须将其还原为"具体动作"与"施动者"。

## 二、 学术结构的听觉化重塑

1.  **融化文献综述**
    *   提取这些文献背后的"思维演进脉络"或"共同指向的矛盾"。将其合并重写。
2.  **抹除视觉结构词**
    *   删除所有诸如"首先、其次、最后"、"综上所述"、"一方面、另一方面"等依赖视觉占位的结构词。
    *   替换为听觉逻辑粘合剂。

## 三、 认知节奏控制

1.  **密度稀释与自然冗余**
    *   每当你输出完一个复杂的因果推理链之后，必须插入一句简短的"降维总结句"。
2.  **客观张力替代虚假互动**
    *   保持学术的客观与冷峻，严禁使用"想象一下"、"大家知道吗"等刻意互动的播客腔调。

## 四、 运行环境与输入

**【全局认知坐标】**
- 当前航向（本集主题）：{episode['title']}
- 核心逻辑主轴：{episode['central_question']}
- 必须锚定的关键概念：{format_list(episode.get('key_concepts', []))}

**【当前处理区块】**
- 原始高密度文本：
{full_text}

---
请严格执行上述引擎法则，忽略具体领域差异，直接输出松弛、自然、逻辑严密的阐释性口语文本流。不输出任何格式标签、分析过程或额外解释。
'''


def script_rewrite_hardcore(episode: dict, book_data: dict, client=None) -> str:
    if client is None:
        client = get_llm_client()

    from script.utils import extract_chapters
    chaps = episode.get("chapters", [])
    chapters = extract_chapters(book_data)
    chap_ids = [x.split("：")[0] for x in chaps]
    full_text = " ".join([chapters[int(cid)]["body"] for cid in chap_ids if cid.isdigit()])
    original_len = len(full_text)
    min_required_len = original_len // 3

    for attempt in range(1, 4):
        prompt = _build_hardcore_prompt(episode, full_text)
        print(f"正在生成台本：{episode['title']} (尝试 {attempt}/3)...")
        script = llm_call(prompt, client)
        script_len = len(script)
        print(f"Generated {script_len} words from original {original_len} words")
        if script_len >= min_required_len:
            return script
        print(f"警告：输出 {script_len} 字 < 最小要求 {min_required_len} 字，准备重试...")

    raise RuntimeError(f"脚本生成失败")


def _build_hardcore_prompt(episode: dict, full_text: str) -> str:
    return f'''
**[Role & Objective]**
你是一位书籍解读者与知识重建者。你要将书籍内容整理组织成一场播客的台本。你的任务不是总结或提炼，而是忠实重构作者的思想脉络，将给定文本改写为适合长篇单口播客的口述文稿。

**[Core Principles]**
**忠实优先**：最高优先是如实还原作者的思考。
**思想重建**：把文本看作作者思维过程的压缩包。
**隐含前提揭示**：主动识别作者默认接受的前提。
**评论原则**：评论仅用于帮助听众理解原著的价值与边界。

**[Output Format]**
文稿直入TTS系统，必须满足：
1. 纯语音流：无标题、小标题、章节号、Markdown、项目符号、括号说明等。
2. 去视觉化：禁用"如下""上面提到""下图"等依赖版面的词。
3. 语言克制：禁用"震惊""颠覆认知""炸裂"等浮夸表达。
4. 面对聪明但无专业训练的听众。

**[Narrative Architecture]**
第一阶段：认知张力 -> 第二阶段：背景与脉络 -> 第三阶段：论证链重建 -> 第四阶段：隐含结构揭示 -> 第五阶段：沉淀与回望

**[Input Area]**
【当前单集主题】{episode['title']}
【当前单集概要】{episode.get('summary', '')}
【原始文本】{full_text}

任务指令：严格遵循以上原则，将原文重构为一篇完整、连续、适合长篇单口播客的思想口述稿。最终输出15000至20000字左右，直接输出正文。
'''

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from dotenv import load_dotenv
import pdb
from text_process.utils import extract_chapters, split_chunks
from utils import load_json, write_text, load_text, json_eval

load_dotenv()

OUTLINE_PATH = "asset/ten_eco/outline.json"
BOOK_PATH = "asset/ten_eco/ten_eco.json"
OUTPUT_DIR = "asset/ten_eco"

client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")


def llm_call(prompt):
    """调用 LLM 生成播客台本"""
    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[{"role": "user", "content": prompt}],
        stream=False,
        max_tokens=65536,
        reasoning_effort="high",
        extra_body={"thinking": {"type": "enabled"}}
    )
    return response.choices[0].message.content

def script_rewrite(episode, max_retries=3):
    chaps = episode['chapters']
    chap_ids = [x.split('：')[0] for x in chaps]
    full_text = ' '.join([book_data[chap_id]['body'] for chap_id in chap_ids])
    original_len = len(full_text)
    min_required_len = original_len // 3
    
    for attempt in range(1, max_retries + 1):
        prompt = f'''
**[Role & Objective]**
你是一位书籍解读者与知识重建者。你要将书籍内容整理组织成一场播客的台本。你的任务不是总结或提炼，而是忠实重构作者的思想脉络，将给定文本改写为适合长篇单口播客的口述文稿。你要帮助听众理解：作者观察到什么问题、为何关注它、依赖哪些前提与背景、如何一步步推导出结论、该结论在其整体思考中的位置。你可以谨慎地从今日视角进行评析，但必须以理解作者本意为先，评论克制且点到为止。

**[Core Principles]**
**忠实优先**：最高优先是如实还原作者的思考。允许补充作者省略的背景、压缩的推理、必要的类比，但禁止以其他学说替代作者本意，或脱离原著进行无关发散。允许谨慎指出作者的时代局限，前提是不歪曲原意且有助于深层理解。
**思想重建**：把文本看作作者思维过程的压缩包。面对重要观点，优先追问：它为何出现？解决什么难题？立足哪些前提？如何推导得到？需补全隐含环节，而非直接展示结论。
**隐含前提揭示**：主动识别作者默认接受的前提——如对人、社会、市场、技术等的基本预设，继承或反对的既有观点。这些往往比显性结论更关键。
**评论原则**：评论仅用于帮助听众理解原著的价值与边界。必须建立在充分理解作者的基础上，措辞保守、节制，避免喧宾夺主。对时代局限的指陈应扎根于原作自身逻辑的断裂或盲点，而不是套用当下标准简单裁判。

**[Output Format]**
文稿直入TTS系统，必须满足：
1. 纯语音流：无标题、小标题、章节号、Markdown、项目符号、括号说明、舞台指令、音效提示、注释等。输出连续可朗读的正文。
2. 去视觉化：禁用“如下”“上面提到”“下图”“本部分”等依赖版面的词，依靠思维逻辑自然推进。
3. 语言克制：禁用“震惊”“颠覆认知”“炸裂”等浮夸表达。力量源于事实、逻辑与推演。
4. 面对聪明但无专业训练的听众：不俯视不简化，专业概念首次出现时自然解释。避免学术论文腔，用口语传递深度。

**[Narrative Architecture]**
第一阶段：认知张力。从核心问题切入，呈现作者试图解释的现象、挑战的成见或解决的理论难题。让问题先站住脚，使听众感到讨论的必要。
第二阶段：背景与脉络。交代问题出现的土壤：时代氛围、既有看法的局限，以及作者为何认为旧说法不够用。补充的背景必须服务于后续论证。
第三阶段：论证链重建。逐层展开推理，不跳步、不抢先给答案。每个关键结论都先摆前提，再展推导，后呈结果。还原作者的思维路径。
第四阶段：隐含结构揭示。点出作者未明言的部分：信赖的理论前提、研究方法、价值取向以及对世界运作方式的根本假设。
第五阶段：沉淀与回望。收束时回应：我们真正理解了什么、哪些疑惑已解、哪些仍敞开，该观点在全书及更宽思想版图中的位置。可极其克制地提及当下回望该思想时的洞见或局限，但勿变为主角。

**[Narrative Style]**
推理优先，展示观察—假设—验证—修正—收束的过程。主播退居幕后，仅在有助于推进理解时极少量插入“我们”“你”等第一二人称。可谨慎使用“这里我们不妨停下来想一下”等引导句式。对于抽象概念，先解释、拆解、重述，再前行，允许适度重复。可用类比帮助理解，但必须精准且不扭曲原意，宁可牺牲生动也不牺牲准确。

**[Length Expansion Rules]**
扩写只允许来自：A.补充作者默认省略的背景知识；B.展开压缩的论证步骤；C.增加助解的案例与类比；D.揭示作者未明言但实际依赖的前提。禁止通过重复、同义改写、情绪渲染、空洞感慨、观点复读等方式填充字数。目标是提升思想密度与理解深度。

**[Input Area]**
【当前单集主题】{episode['title']}
【当前单集概要】{episode['summary']}
【原始文本】{full_text}

任务指令：严格遵循以上原则，将原文重构为一篇完整、连续、适合长篇单口播客的思想口述稿。最终输出15000至20000字左右，直接输出正文。
'''
        print(f'正在生成台本：{episode["title"]} (尝试 {attempt}/{max_retries})...')
        script = llm_call(prompt)
        script_len = len(script)
        print(f"Generated {script_len} words from original {original_len} words text")
        
        if script_len >= min_required_len:
            return script
        else:
            print(f"警告：生成的台本长度 {script_len} 字小于最小要求 {min_required_len} 字 ({script_len / original_len:.1%})，准备重试...")
    
    raise RuntimeError(f"脚本生成失败：经过 {max_retries} 次重试，输出长度仍未达到最小要求（需 >= {min_required_len} 字）")

def _audit_chunk(idx, total, chunk, max_retries=3):
    """单个 chunk 的审校任务（可并行执行，超过10%变化会重试）"""
    chunk_ori_len = len(chunk)
    
    for attempt in range(1, max_retries + 1):
        print(f"audit: chunk {idx + 1}/{total}, chars={chunk_ori_len}, 尝试 {attempt}/{max_retries}")
        prompt = f'''
**[Role & Objective]**
你是一名顶级的中文播客台本编辑。你需要深入阅读理解传入的【播客台本片段】，对其进行内容审校，并输出经过审阅与纠偏的【完整台本片段】。

请严格执行以下两大模块的编辑任务：

### 模块一：身份视角校准（内容编审）
当前片段可能混淆了"播客主播"与"原书作者"的身份。在没有任何外部背景信息的情况下，你必须依靠文本内的逻辑线索进行精准切割：
1. **剥离作者身份**：原书作者的经历、写作行为、职业背景、亲身观察、个人判断与遭遇，**绝对不能**以"我"的第一人称出现。请将其转换为自然的第三方表述（如"作者写道"、"作者回忆"、"书中提到"、"这位作者指出"等，请根据语境灵活遣词）。
2. **保留主播身份**：只有播客主讲人的阅读感受、讲述引导、互动提问、转场串词等，才可以保留"我"的自称。
3. **精准打击**：切忌机械替换全篇的"我"，必须逐句推敲每一个"我"的真实指代。

### 模块二：TTS 朗读纯净度（后期制作）
将文本转化为"听觉友好"的极致口语状态：
1. **数字全汉字化**：将所有阿拉伯数字、百分号、小数、年份/年代、范围、金额、单位、序号，全部转换为自然中文读法（例：1998年 -> 一九九八年；50.5% -> 百分之五十点五；1~2个 -> 一个到两个）。非必要不保留任何数字，如遇必须保留的专有标识，需改写为可顺畅朗读的表达。
2. **多音字/异读词规避**：主动识别并消除所有可能导致 TTS 引擎读错的歧义词、多音字和冷僻专名。**严禁使用拼音或括号注音**，必须通过**"同义词替换"**或**"语序微调"**的方式，将其改写为自然、无歧义且忠于原意的中文表达。（注：若某多音字在当前语境下读音极度稳定，可不改写以避免过度修改）。
3. **视觉符号清理**：清除括号注、无法朗读的标点及视觉排版格式，保留适合语音停顿的自然标点。

### ⚠️ 绝对禁忌（Guardrails）
- 不要压缩摘要，不要扩写发散。
- 严禁改变原有的事实逻辑与讲述顺序。
- 严禁破坏台本内容和表达，仅做上面两个模块的校正，其余保持原样。

【当前片段】
{chunk}

### 输出规范
请严格按照以下 JSON 格式返回，不要包含任何 Markdown 代码块标记（如 ```json），直接返回纯 JSON 字符串：
{{
    "text": "经过审校纠正的台本",
    "review_log": "纠偏的记录，逐条说明做了哪些修改。若无需修改，请填写'未发现问题'"
}}
'''
        reviewed_chunk_dict = json_eval(llm_call(prompt))
        reviewed_chunk_len = len(reviewed_chunk_dict['text'])
        change_ratio = (reviewed_chunk_len / chunk_ori_len - 1)
        print(f"审校结束，由{chunk_ori_len}个字变为{reviewed_chunk_len}个字, 变化幅度{change_ratio:.2%}, 审校日志: {reviewed_chunk_dict['review_log']}")
        
        if reviewed_chunk_len <= chunk_ori_len * 1.1 and reviewed_chunk_len >= chunk_ori_len * 0.9:
            return (idx, reviewed_chunk_dict['text'])
        else:
            print(f"警告：Chunk {idx + 1} 审校后文本长度变化超过10%（{change_ratio:.2%}），原长={chunk_ori_len}，新长={reviewed_chunk_len}，准备重试...")
    
    raise ValueError(f"Chunk {idx + 1}: 经过 {max_retries} 次重试，审校后文本长度变化仍超过10%")

def audit_script_parallel(script, chunk_chars=4500, max_workers=4):
    """并行审校所有 chunk，按顺序组装结果"""
    chunks = split_chunks(script, max_chars=chunk_chars)
    total = len(chunks)
    results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_audit_chunk, idx, total, chunk): idx 
            for idx, chunk in enumerate(chunks)
        }
        
        for future in as_completed(futures):
            try:
                idx, reviewed_text = future.result()
                results[idx] = reviewed_text
            except ValueError as e:
                raise RuntimeError(f"审校失败：{str(e)}")
    
    # 按原始顺序组装
    reviewed = [results[i] for i in range(total)]
    return "\n\n".join(reviewed)

def audit_script(script, chunk_chars=4500):
    """对外接口：隐藏并行复杂度"""
    return audit_script_parallel(script, chunk_chars=chunk_chars)

if __name__ == '__main__':
    # outline = load_json(OUTLINE_PATH)
    book_data = extract_chapters(load_json(BOOK_PATH))
    pdb.set_trace()

    for episode in outline['episodes']:
        episode_id = episode['episode_id']
        episode_draft_path = f'{OUTPUT_DIR}/{episode_id}_script_draft.txt'
        episode_final_path = f'{OUTPUT_DIR}/{episode_id}_script_final.txt'
        if os.path.exists(episode_final_path):
            print(f"已存在最终稿，跳过生成：{episode_final_path}")
            continue
        import pdb; pdb.set_trace()
        if os.path.exists(episode_draft_path):
            script_draft = load_text(episode_draft_path)
        else:
            script_draft = script_rewrite(episode)
            write_text(episode_draft_path, script_draft)
        print(f"台本初稿已生成，长度 {len(script_draft)} 字")
        print(f"正在审校台本：{episode['title']}...")
        script_final = audit_script(script_draft)
        write_text(episode_final_path, script_final)

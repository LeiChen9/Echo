import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from dotenv import load_dotenv

from text_process.utils import extract_chapters, split_chunks
from utils import load_json, write_text, load_text, json_eval

load_dotenv()

OUTLINE_PATH = "asset/reason_op/outline.json"
BOOK_PATH = "asset/reason_op/reason_op.json"
OUTPUT_DIR = "asset/reason_op"

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
# Role: 声音纪录片导演 & 知识勘探者 (Audio-Doc Director & Knowledge Prospector)

## 1. 核心定位与三层身份边界 (Core Identity & 3-Layer Boundary)
你的任务是将书面文本逆向工程为适合听觉的单口播客台本。你要带着听众重走作者思维路径的**引路人 (Cognitive Guide)**。

你的讲述状态是**平静、向内收敛的**。这档播客的起点，源自你察觉到了某种“生活的异常”或“经验的断层”，而你正试图通过阅读这本书籍，来抚平这种异常。你在话筒前的状态，是在进行一场**自我的勘探**，并平静地向听众展示这个勘探的旅程。

在任何时刻，必须严格坚守以下三层身份的物理隔离：
* **第一层：作者 (The Author)**。负责提出观点、建立理论、提供证据。必须使用“作者发现”、“原书向我们展示了”等客体化表述。
* **第二层：主讲人 (You)**。负责观察、解释、补充背景。你的主观认知只能作为“理解作者”的辅助脚手架。
* **第三层：听众 (The Audience)**。他们是与你并肩同行的智识伙伴。**请假定他们具备一流高校大一新生的逻辑理解力，但没有任何特定专业的学术背景。**你的职责是陪他们抵达答案，而不是单向宣读答案。

**【绝对红线：纯净听觉与盲视约束】**
当前输出将直接送入 TTS 引擎，必须做到绝对纯净：
* **禁止任何非发音字符**：严禁 Markdown 标题符号（#）、加粗符号（**）、列表编号及任何括号内的舞台/情绪指示符。
* **纯听觉锚定**：严禁使用“如下图”、“前面写道”等视觉空间指代。所有图表、公式必须转化为唤起想象力的纯听觉描述。

## 2. 叙事引擎与认知链条 (Narrative Engine & Cognitive Chain)
你的工作是组织认知，而非单纯组织语言。
* **前置认知自检 (Consciousness Check)**：在生成每一段内容前，必须隐式回答三个问题：当前在解决什么问题？为何必须在此处展开？听众听完多理解了什么？若无法回答，则剔除该段落。
* **闭环叙事节奏 (Closed-loop Rhythm)**：每一个核心知识点，必须强行展开为以下完整链条，结论必须像植物一样自然生长出来，禁止提前宣布：
  现象引入 -> 建立疑问 -> 补充隐含背景 -> 展示作者的推理齿轮 -> 形成阶段认知 -> 抛出下一环问题。

## 3. 执行策略与工作记忆管理 (Execution & Working Memory)
* **隐性知识补完 (Implicit Knowledge Expansion)**：作者在写作时往往会预设读者具备某些专业前提。**你必须敏锐识别出这些高于“大一新生知识基线”的断层**，主动承担背景补完的职责。补充那些作者默认存在却未明确表达的历史背景或理论前提，辅助推理链顺利闭环（补完原则是“按需加载”，绝不无边界拓展）。
* **基于物证的重构 (Evidence-Driven Reconstruction)**：像拆解精密机械一样解压复杂理论。作者提供什么证据，就带听众看什么证据；一个齿轮一个齿轮地展示因果关系，让推理本身产生碾压级的说服力。
* **受控偏航 (Controlled Tangent)**：允许为了补充背景而暂时离开主线去讲述历史切片或现实案例。这部分可以由你的主观认知来补充，但任何偏航必须像橡皮筋，拉开后必须用一句干脆的逻辑陈述瞬间弹回主线，重新对齐当前问题。
* **工作记忆同步 (Working Memory Management)**：播客无法翻页。在经历一段复杂推理后，必须主动执行状态同步（“所以我们说到这里，其实核心就是……”），确保听众不掉队。

## 4. 语言指纹与勘探质感 (Language Fingerprint & Prospecting Vibe)
* **绝对摒弃廉价情绪与表演**：禁止使用廉价的情绪词。保持面对复杂系统时的静气与通透。真正的力量来自于逻辑本体被剥丝抽茧后的呈现，而非主讲人的声带震动。
* **日常感与思维的毛边 (Vocal Realism)**：生活化的叙述并非为了套近乎，而是还原一个人在深夜思考时的真实状态。必须完全摒弃播音腔和 AI 式的端庄：
  * **允许口语垫音**：在抛出复杂逻辑或进行思考转折时，允许极其自然地出现“就是”、“那个”、“其实”、“对”等词汇。
  * **允许脑部延时 (Cognitive Lag)**：在进入关键概念前，允许出现克制的词语重复或磕巴，表现思维正在组织语言的真实阻力（例如：“在这个、在这个框架里……”）。
* **概念降维与物理锚定**：面对超过大一新生认知阈值的专业术语或高度抽象概念，必须宕开一笔进行“物理降维”。**将其映射为具有明确物理反馈的日常比喻或生活经验**，解释透彻后再干脆地带回主线。
* **评论纪律**：评论仅限用于揭示隐蔽逻辑或连接生活经验。你的态度应该是平静且克制的。

## 5. 终局视角 (Ending Perspective)
每当完成一段关键推理或临近单集尾声，不要急于下课。带着听众站在新建立的认知高地上进行回头俯瞰。指明原书是如何精准地抚平了我们在开篇遇到的那一个“生活的异常”。不重复具体知识，而是将该知识泛化为一种理解真实世界的新范式，接纳人类共有的某种认知规律。

---

## 6. 运行时上下文 (Runtime Context)

**【当前单集航向 (Episode Compass)】**
* 核心主题：{episode.get('title', '未提供')}
* 试图抚平的异常/核心问题：{episode.get('central_question', '未提供')}
* 本集必须达成的认知闭环：{episode.get('ending_takeaway', '未提供')}

**【前置认知状态 (Previous Context)】**
{previous_context if previous_context else "这是本集的开篇。请从一个你所察觉到的生活异常、现象悖论或一段极其个人的经验切入，平静地开启这场勘探。"}

**【本轮待解剖的文本切片 (Source Chunk)】**
{current_chunk}

---
请基于上述协议，直接输出纯口述的策展台本。
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
    outline = load_json(OUTLINE_PATH)
    book_data = extract_chapters(load_json(BOOK_PATH))

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

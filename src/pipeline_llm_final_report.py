import os
import json
from pathlib import Path
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
IN_JSON = ROOT / "data" / "outputs" / "gap_summary.json"
OUT_MD = ROOT / "data" / "outputs" / "final_report.md"

api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise ValueError("未检测到环境变量 DASHSCOPE_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

def build_prompt(payload: dict) -> str:
    # 只放必要信息，避免prompt太长
    top_missing = payload.get("top_missing", [])[:12]
    city_top10 = payload.get("city_top10", [])[:10]
    city_salary = payload.get("city_salary", [])[:10]
    edu = payload.get("edu_dist", [])
    exp = payload.get("exp_dist", [])

    return f"""
你是资深数据分析/AI工作流面试辅导顾问。请基于下面的结构化数据，生成一份“可直接发给HR/面试官”的求职项目报告（Markdown 格式）。
要求：
1) 报告必须结构化，包含标题、摘要、关键结论、数据证据（用小表格/要点），以及“我如何用这个系统做决策”
2) 重点体现：Excel导入→标准化→技能抽取（LLM）→分层加权匹配→自动分级→输出建议 的闭环
3) 明确写出：当前匹配等级、三层匹配度、Top缺失技能（按权重），并给出 4 周 / 8 周 / 12 周行动计划
4) 输出一个“给HR的3句话版本”（可直接复制到BOSS聊天）
5) 语言：中文，专业但不装，重点突出“可运行、可复用、可解释”
6) 不要编造不存在的数据；只能使用提供的数据推导结论

【结构化数据】
- 综合匹配度 overall_match: {payload.get("overall_match", 0):.4f}
- Level: {payload.get("level", "")}
- Core match: {payload.get("core_match", 0):.4f}
- Extended match: {payload.get("extended_match", 0):.4f}
- Premium match: {payload.get("premium_match", 0):.4f}
- 用户技能 user_skills: {payload.get("user_skills", [])}

- Top缺失技能（skill/tier/weight/freq）:
{top_missing}

- 城市岗位Top10:
{city_top10}

- 城市平均月薪K Top10:
{city_salary}

- 学历分布:
{edu}

- 经验分布:
{exp}
""".strip()

def main(model="qwen-plus"):
    payload = json.loads(IN_JSON.read_text(encoding="utf-8"))
    prompt = build_prompt(payload)

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你输出的是可交付的Markdown报告，务必可直接用于求职沟通。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    md = resp.choices[0].message.content.strip()
    OUT_MD.write_text(md, encoding="utf-8")
    print("✅ 已生成最终报告：", OUT_MD)

if __name__ == "__main__":
    main()
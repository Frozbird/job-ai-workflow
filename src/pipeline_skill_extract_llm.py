import os
import time
from pathlib import Path
import pandas as pd
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]

IN_XLSX = ROOT / "data" / "processed" / "jobs_standardized.xlsx"
OUT_XLSX = ROOT / "data" / "processed" / "jobs_with_skills.xlsx"

api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise ValueError("未检测到环境变量 DASHSCOPE_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 简单技能标准化映射（可持续扩展）
SKILL_MAP = {
    "power bi": "PowerBI",
    "powerbi": "PowerBI",
    "pandas": "Pandas",
    "numpy": "Numpy",
    "postgresql": "PostgreSQL",
    "postgre sql": "PostgreSQL",
    "a/b测试": "A/B测试",
    "ab测试": "A/B测试",
    "rag": "RAG",
    "prompt": "Prompt",
}

def normalize_skills(text: str) -> str:
    if not text:
        return ""
    items = []
    for s in str(text).replace("，", ",").split(","):
        s = s.strip()
        if not s:
            continue
        key = s.lower()
        s = SKILL_MAP.get(key, s)
        items.append(s)
    # 去重但保持顺序
    seen = set()
    out = []
    for s in items:
        if s not in seen:
            out.append(s)
            seen.add(s)
    return ",".join(out)

def llm_extract_skills(job_title: str, job_desc: str) -> str:
    prompt = f"""
请从以下岗位描述中抽取“硬技能/工具/方法论”（例如：SQL、Python、Pandas、数据仓库、A/B测试、Spark、Tableau、RAG、API调用等）。
要求：
- 只输出技能列表
- 用英文逗号分隔
- 不要输出解释、不要输出编号、不要输出多余文字
岗位：{job_title}
描述：{job_desc}
""".strip()

    resp = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": "你是严谨的信息抽取助手，只输出要求的技能列表。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()

def run_skill_extract(limit: int | None = None, sleep_sec: float = 0.3):
    df = pd.read_excel(IN_XLSX)

    # ✅ 确保关键列存在并且是字符串类型
    for col in ["skills_text", "job_title", "job_desc"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].astype("string")

    if limit is not None:
        df = df.head(limit).copy()

    # 优先用现成 skills_text；为空才用 LLM 抽
    filled = 0
    for i, row in df.iterrows():
        if isinstance(row.get("skills_text"), str) and row["skills_text"].strip():
            df.at[i, "skills_text"] = normalize_skills(row["skills_text"])
            continue

        title = str(row.get("job_title") or "").strip()
        desc = str(row.get("job_desc") or "").strip()

        if not desc:
            df.at[i, "skills_text"] = ""
            continue

        skills = llm_extract_skills(title, desc)
        df.at[i, "skills_text"] = normalize_skills(skills)
        filled += 1

        # 控制频率，避免过快
        time.sleep(sleep_sec)

    OUT_XLSX.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(OUT_XLSX, index=False)
    print("✅ 已输出带技能的Excel：", OUT_XLSX)
    print("本次使用LLM抽取条数：", filled)

if __name__ == "__main__":
    run_skill_extract(limit=20)
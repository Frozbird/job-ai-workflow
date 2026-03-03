import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# 你后面只要把 input_jobs.xlsx 换成用户真实文件名即可
DEFAULT_INPUT = ROOT / "data" / "input" / "jobs_input.xlsx"
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "jobs_standardized.xlsx"

CANONICAL = [
    "job_title", "city", "salary_text", "experience", "education",
    "company_name", "industry", "job_desc", "skills_text"
]

# 半结构化列名映射：关键词越靠前优先级越高
RULES = {
    "job_title": ["岗位", "职位", "title", "job", "名称"],
    "city": ["城市", "地区", "location", "工作地点"],
    "salary_text": ["薪资", "月薪", "年薪", "工资", "salary", "k薪"],
    "experience": ["经验", "年限", "工作经验"],
    "education": ["学历", "学位", "教育背景"],
    "company_name": ["公司", "企业", "company"],
    "industry": ["行业", "领域"],
    "job_desc": ["描述", "职责", "岗位描述", "工作内容", "jd", "job desc", "职位描述"],
    "skills_text": ["技能", "技术栈", "要求", "任职要求", "能力要求"],
}

def _normalize_col(c: str) -> str:
    return re.sub(r"\s+", "", str(c).strip().lower())

def guess_mapping(columns):
    norm_cols = {c: _normalize_col(c) for c in columns}
    mapping = {}
    used = set()

    for target, keys in RULES.items():
        best = None
        for col, ncol in norm_cols.items():
            if col in used:
                continue
            for k in keys:
                if _normalize_col(k) in ncol:
                    best = col
                    break
            if best:
                break
        if best:
            mapping[best] = target
            used.add(best)

    return mapping

def run_excel_import(input_path: Path = DEFAULT_INPUT, output_path: Path = DEFAULT_OUTPUT):
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(input_path)

    mapping = guess_mapping(df.columns)
    df = df.rename(columns=mapping)

    # 保证标准字段都存在（缺失就补空列）
    for col in CANONICAL:
        if col not in df.columns:
            df[col] = None

    df = df[CANONICAL]

    df.to_excel(output_path, index=False)
    print("✅ 已标准化输出：", output_path)

    missing_core = [c for c in ["job_title", "job_desc"] if df[c].isna().all()]
    if missing_core:
        print("⚠ 警告：关键字段缺失/全空：", missing_core, "（LLM抽取技能依赖 job_desc）")

if __name__ == "__main__":
    run_excel_import()
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

IN_PATH = ROOT / "data" / "raw" / "jobs_sample_1000.csv"
OUT_PATH = ROOT / "data" / "processed" / "jobs_cleaned.csv"

def parse_salary(s: str):
    """
    解析形如：
    - 15-25K·14薪
    - 20-35K
    返回：min_k, max_k, months
    """
    if pd.isna(s):
        return None, None, None

    s = str(s).strip()

    # 提取 15-25K
    m = re.search(r"(\d+)\s*-\s*(\d+)\s*[kK]", s)
    if not m:
        return None, None, None

    min_k = int(m.group(1))
    max_k = int(m.group(2))

    # 提取 13薪/14薪
    m2 = re.search(r"·\s*(\d+)\s*薪", s)
    months = int(m2.group(1)) if m2 else 12

    return min_k, max_k, months

def main():
    df = pd.read_csv(IN_PATH, encoding="utf-8-sig")

    print("原始行数：", len(df))

    # 去重（以公司+岗位+城市粗略去重）
    df = df.drop_duplicates(subset=["company_name", "job_title", "city"])

    # 解析薪资
    parsed = df["salary_text"].apply(parse_salary)
    df["min_k"] = parsed.apply(lambda x: x[0])
    df["max_k"] = parsed.apply(lambda x: x[1])
    df["months"] = parsed.apply(lambda x: x[2])

    # 计算年薪区间（单位：K/月 -> K/年）
    df["min_annual_k"] = df["min_k"] * df["months"]
    df["max_annual_k"] = df["max_k"] * df["months"]

    # 生成薪资中位数（用于排序/分析）
    df["mid_k"] = (df["min_k"] + df["max_k"]) / 2.0

    # 基础清洗：去空
    df = df[df["job_title"].notna()]
    df = df[df["city"].notna()]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    print("清洗后行数：", len(df))
    print("已输出：", OUT_PATH)

    # 快速自检：看前 5 行关键字段
    print(df[["job_title","city","salary_text","min_k","max_k","months","min_annual_k","max_annual_k"]].head())

def run_clean():
    main()

if __name__ == "__main__":
    main()
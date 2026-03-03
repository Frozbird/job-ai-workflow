import random
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

def weighted_choice(items):
    # items: [(value, weight), ...]
    values = [v for v, w in items]
    weights = [w for v, w in items]
    return random.choices(values, weights=weights, k=1)[0]

def make_salary_k(exp: str, city_tier: str):
    """
    返回类似: '15-25K·14薪' / '20-35K' / '12-18K·13薪'
    """
    # base by experience
    exp_base = {
        "应届/1年内": (8, 16),
        "1-3年": (12, 24),
        "3-5年": (18, 35),
        "5-10年": (25, 50),
    }
    lo, hi = exp_base.get(exp, (10, 20))

    # city tier multiplier
    tier_mul = {
        "一线": 1.15,
        "新一线": 1.05,
        "二线": 0.95,
        "其他": 0.85,
    }.get(city_tier, 1.0)

    lo = max(6, int(lo * tier_mul))
    hi = max(lo + 2, int(hi * tier_mul))

    # add randomness
    lo = max(6, lo + random.randint(-2, 2))
    hi = max(lo + 2, hi + random.randint(-3, 3))

    # clamp
    lo = min(lo, 60)
    hi = min(hi, 80)

    salary = f"{lo}-{hi}K"

    # some have薪数
    if random.random() < 0.55:
        months = random.choice([12, 13, 14, 15, 16])
        salary += f"·{months}薪"
    return salary

def extract_skills():
    core = ["Python", "SQL", "Pandas", "Numpy"]
    optional = [
        "Tableau", "PowerBI", "Excel", "统计学", "A/B测试", "用户增长",
        "Hive", "Spark", "ClickHouse", "MySQL", "PostgreSQL",
        "机器学习", "XGBoost", "因果推断", "数据建模",
        "数据仓库", "指标体系", "埋点", "ETL",
        "大模型", "Prompt", "RAG", "API调用"
    ]
    # 保证 core 出现
    picked = set(core)
    # 按概率再挑 4~10 个
    extra_n = random.randint(4, 10)
    picked.update(random.sample(optional, k=extra_n))

    # 偶尔加 R / BI
    if random.random() < 0.25:
        picked.add("R")
    if random.random() < 0.25:
        picked.add("BI")

    return ",".join(sorted(picked))

def make_job_title():
    titles = [
        ("数据分析师（Python）", 30),
        ("Python数据分析师", 25),
        ("商业数据分析", 12),
        ("用户增长数据分析", 10),
        ("数据分析（BI方向）", 8),
        ("数据分析实习生", 6),
        ("数据分析（大模型方向）", 9),
    ]
    return weighted_choice(titles)

def main(n=1000, seed=42):
    random.seed(seed)

    cities = [
        ("北京", "一线", 12),
        ("上海", "一线", 12),
        ("深圳", "一线", 10),
        ("广州", "一线", 8),
        ("杭州", "新一线", 10),
        ("成都", "新一线", 8),
        ("南京", "新一线", 7),
        ("武汉", "新一线", 6),
        ("西安", "新一线", 5),
        ("苏州", "二线", 4),
        ("厦门", "二线", 3),
        ("天津", "二线", 3),
        ("长沙", "二线", 3),
        ("重庆", "新一线", 6),
    ]

    exp_levels = [
        ("应届/1年内", 18),
        ("1-3年", 45),
        ("3-5年", 25),
        ("5-10年", 12),
    ]

    edu_levels = [
        ("大专", 6),
        ("本科", 72),
        ("硕士", 20),
        ("博士", 2),
    ]

    industries = [
        ("互联网", 35),
        ("电商", 10),
        ("金融科技", 10),
        ("SaaS/企业服务", 12),
        ("智能制造", 8),
        ("教育", 6),
        ("医疗健康", 6),
        ("游戏", 5),
        ("物流", 4),
        ("其他", 4),
    ]

    company_prefix = ["星环", "云图", "海豚", "极光", "智联", "北辰", "远望", "玄武", "启明", "蓝鲸", "赤兔", "飞梭"]
    company_suffix = ["科技", "数据", "智能", "信息", "网络", "互娱", "金融", "电商", "医疗", "教育"]
    company_tail = ["有限公司", "股份有限公司"]

    rows = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for _ in range(n):
        city, tier = weighted_choice([((c, t), w) for c, t, w in cities])
        exp = weighted_choice(exp_levels)
        edu = weighted_choice(edu_levels)

        title = make_job_title()
        salary = make_salary_k(exp, tier)

        industry = weighted_choice(industries)
        company = f"{random.choice(company_prefix)}{random.choice(company_suffix)}{random.choice(company_tail)}"

        skills = extract_skills()

        # 简短 JD 文本（用于后续技能提取/LLM 报告）
        jd = f"负责{title}相关工作，要求熟练{skills}，具备数据分析与业务沟通能力。"

        rows.append({
            "job_title": title,
            "salary_text": salary,
            "city": city,
            "city_tier": tier,
            "experience": exp,
            "education": edu,
            "company_name": company,
            "industry": industry,
            "skills_text": skills,
            "job_desc": jd,
            "source": "synthetic",
            "crawl_time": now,
        })

    df = pd.DataFrame(rows)

    out = ROOT / "data" / "raw" / "jobs_sample_1000.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, encoding="utf-8-sig")

    print("生成完成：", out)
    print("行数：", len(df))
    print("列：", list(df.columns))

def run_generate(n=1000, seed=42):
    main(n=n, seed=seed)
    
if __name__ == "__main__":
    main(n=1000, seed=42)
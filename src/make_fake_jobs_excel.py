import random
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "input" / "jobs_input.xlsx"

def weighted_choice(items):
    vals = [v for v, w in items]
    ws = [w for v, w in items]
    return random.choices(vals, weights=ws, k=1)[0]

def make_salary(exp: str, tier: str):
    base = {
        "应届/1年内": (8, 16),
        "1-3年": (12, 24),
        "3-5年": (18, 35),
        "5-10年": (25, 50),
    }
    lo, hi = base.get(exp, (10, 20))
    mul = {"一线": 1.15, "新一线": 1.05, "二线": 0.95, "其他": 0.85}.get(tier, 1.0)
    lo = max(6, int(lo * mul) + random.randint(-2, 2))
    hi = max(lo + 2, int(hi * mul) + random.randint(-3, 3))
    months = random.choice([12, 13, 14, 15]) if random.random() < 0.6 else 12
    s = f"{lo}-{hi}K"
    if months != 12:
        s += f"·{months}薪"
    return s

def make_skills():
    core = ["Python", "SQL", "Pandas", "Numpy"]
    opt = [
        "Excel", "PowerBI", "Tableau", "MySQL", "PostgreSQL",
        "数据仓库", "指标体系", "ETL", "埋点", "A/B测试", "用户增长",
        "Spark", "Hive", "ClickHouse",
        "机器学习", "XGBoost", "因果推断",
        "大模型", "RAG", "Prompt", "API调用"
    ]
    k = random.randint(5, 10)
    picks = set(core)
    picks.update(random.sample(opt, k=k))
    return ",".join(sorted(picks))

def make_job_desc(title: str, skills: str):
    # 生成“看起来像JD”的文本，供LLM抽取技能
    skill_list = skills.replace(",", "、")
    templates = [
        f"岗位职责：1）负责{title}相关的数据提取、清洗与分析；2）搭建指标体系与看板，输出业务洞察；3）配合产品/运营完成A/B测试与增长分析。任职要求：熟练掌握{skill_list}，具备良好沟通与推动能力。",
        f"工作内容：围绕业务问题开展数据分析与建模，沉淀可复用分析方法；支持日常报表自动化。要求：掌握{skill_list}，理解SQL多表关联与子查询，能用Python进行数据处理与可视化。",
        f"职责：数据采集与ETL、数据仓库建设支持、专题分析。要求：熟悉{skill_list}，具备指标口径定义经验，有一定机器学习/统计基础者优先。"
    ]
    return random.choice(templates)

def main(n=50, seed=42):
    random.seed(seed)
    OUT.parent.mkdir(parents=True, exist_ok=True)

    cities = [
        ("北京", "一线", 12), ("上海", "一线", 12), ("深圳", "一线", 10), ("广州", "一线", 8),
        ("杭州", "新一线", 10), ("成都", "新一线", 8), ("南京", "新一线", 7), ("武汉", "新一线", 6),
        ("西安", "新一线", 5), ("重庆", "新一线", 6), ("苏州", "二线", 4), ("厦门", "二线", 3),
        ("天津", "二线", 3), ("长沙", "二线", 3),
    ]

    titles = [
        ("数据分析师（Python）", 30),
        ("Python数据分析师", 25),
        ("商业数据分析", 12),
        ("用户增长数据分析", 10),
        ("数据分析（BI方向）", 8),
        ("数据分析（大模型方向）", 9),
        ("数据分析实习生", 6),
    ]

    exp_levels = [("应届/1年内", 18), ("1-3年", 45), ("3-5年", 25), ("5-10年", 12)]
    edu_levels = [("大专", 6), ("本科", 72), ("硕士", 20), ("博士", 2)]

    company_prefix = ["星环", "云图", "海豚", "极光", "智联", "北辰", "远望", "玄武", "启明", "蓝鲸", "赤兔", "飞梭"]
    company_suffix = ["科技", "数据", "智能", "信息", "网络", "互娱", "金融科技", "电商", "医疗", "教育"]
    company_tail = ["有限公司", "股份有限公司"]

    rows = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for _ in range(n):
        city_choice = weighted_choice([(c, w) for c, t, w in cities])
        # 重新找到对应的 tier
        city_name = city_choice
        city_tier = next(t for c, t, w in cities if c == city_name)

        title = weighted_choice(titles)
        exp = weighted_choice(exp_levels)
        edu = weighted_choice(edu_levels)
        salary = make_salary(exp, city_tier)

        company = f"{random.choice(company_prefix)}{random.choice(company_suffix)}{random.choice(company_tail)}"

        skills = make_skills()
        jd = make_job_desc(title, skills)

        rows.append({
            "岗位": title,
            "岗位描述": jd,
            "城市": city_name,
            "薪资": salary,
            "公司": company,
            "学历": edu,
            "经验": exp,
            "_gen_time": now,
        })

    df = pd.DataFrame(rows)
    df.to_excel(OUT, index=False)
    print("✅ 已生成模拟招聘Excel：", OUT)
    print("行数：", len(df))
    print("列：", list(df.columns))

if __name__ == "__main__":
    main(n=50, seed=42)
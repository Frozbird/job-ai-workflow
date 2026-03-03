import os
import sqlite3
import pandas as pd
from pathlib import Path
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "jobs.db"
REPORT_PATH = ROOT / "report.md"

# 读取环境变量
api_key = os.getenv("DASHSCOPE_API_KEY")

if not api_key:
    raise ValueError("未检测到 DASHSCOPE_API_KEY 环境变量")

# 创建客户端（阿里云 OpenAI 兼容接口）
client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

def load_analysis_data():
    conn = sqlite3.connect(DB_PATH)

    city_stats = pd.read_sql("""
        SELECT city, COUNT(*) as job_count,
               ROUND(AVG(mid_k),2) as avg_salary
        FROM jobs
        GROUP BY city
        ORDER BY job_count DESC
        LIMIT 10;
    """, conn)

    edu_stats = pd.read_sql("""
        SELECT education, COUNT(*) as cnt
        FROM jobs
        GROUP BY education
        ORDER BY cnt DESC;
    """, conn)

    exp_stats = pd.read_sql("""
        SELECT experience, COUNT(*) as cnt
        FROM jobs
        GROUP BY experience
        ORDER BY cnt DESC;
    """, conn)

    skill_stats = pd.read_sql("""
        SELECT skill, count
        FROM skill_stats
        ORDER BY count DESC
        LIMIT 20;
    """, conn)

    conn.close()

    return city_stats, edu_stats, exp_stats, skill_stats


def build_prompt(city, edu, exp, skill):
    return f"""
你是一名数据分析行业研究专家。

请根据以下统计数据，生成一份结构化行业分析报告。

【城市岗位与薪资情况】
{city.to_string(index=False)}

【学历分布】
{edu.to_string(index=False)}

【经验分布】
{exp.to_string(index=False)}

【技能Top20】
{skill.to_string(index=False)}

请输出：
1. 市场总体规模分析
2. 城市薪资差异解读
3. 学历与经验结构分析
4. 核心技能趋势分析
5. 对求职者的能力提升建议
6. 未来趋势判断

报告格式使用Markdown。
"""


def generate_report():
    city, edu, exp, skill = load_analysis_data()
    prompt = build_prompt(city, edu, exp, skill)

    response = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": "你是一名专业行业分析师。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    content = response.choices[0].message.content

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print("报告生成完成：", REPORT_PATH)

def run_llm_report():
    generate_report()

if __name__ == "__main__":
    generate_report()
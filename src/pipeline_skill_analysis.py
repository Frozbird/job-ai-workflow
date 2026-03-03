import sqlite3
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "jobs.db"

def main():
    conn = sqlite3.connect(DB_PATH)

    # 读取技能字段
    df = pd.read_sql("SELECT skills_text FROM jobs", conn)

    print("读取技能数据行数：", len(df))

    # 拆分技能
    skill_series = df["skills_text"].str.split(",")

    # 展平
    all_skills = skill_series.explode().str.strip()

    skill_counts = all_skills.value_counts().reset_index()
    skill_counts.columns = ["skill", "count"]
    
    print("\n【技能 Top 20】")
    print(skill_counts.head(20))

    # 保存到数据库
    skill_counts.to_sql("skill_stats", conn, if_exists="replace", index=False)

    conn.close()
    print("\n技能统计已写入数据库 skill_stats 表")

def run_skill():
    main()

if __name__ == "__main__":
    main()
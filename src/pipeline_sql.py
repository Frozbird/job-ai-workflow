import sqlite3
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DB_PATH = ROOT / "jobs.db"
CSV_PATH = ROOT / "data" / "processed" / "jobs_cleaned.csv"

def main():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

    print("准备写入数据库，数据行数：", len(df))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 写入数据库（覆盖旧表）
    df.to_sql("jobs", conn, if_exists="replace", index=False)

    print("数据已写入 SQLite：jobs.db")

    # ======================
    # SQL 分析 1：城市岗位数量
    # ======================
    print("\n【城市岗位数量 Top 10】")
    q1 = """
    SELECT city, COUNT(*) as job_count
    FROM jobs
    GROUP BY city
    ORDER BY job_count DESC
    LIMIT 10;
    """
    print(pd.read_sql(q1, conn))

    # ======================
    # SQL 分析 2：平均薪资（按城市）
    # ======================
    print("\n【各城市平均月薪中位数】")
    q2 = """
    SELECT city, ROUND(AVG(mid_k),2) as avg_mid_k
    FROM jobs
    GROUP BY city
    ORDER BY avg_mid_k DESC;
    """
    print(pd.read_sql(q2, conn))

    # ======================
    # SQL 分析 3：学历分布
    # ======================
    print("\n【学历分布】")
    q3 = """
    SELECT education, COUNT(*) as cnt
    FROM jobs
    GROUP BY education
    ORDER BY cnt DESC;
    """
    print(pd.read_sql(q3, conn))

    # ======================
    # SQL 分析 4：经验分布
    # ======================
    print("\n【经验要求分布】")
    q4 = """
    SELECT experience, COUNT(*) as cnt
    FROM jobs
    GROUP BY experience
    ORDER BY cnt DESC;
    """
    print(pd.read_sql(q4, conn))

    conn.close()
    print("\n数据库连接已关闭")

def run_sql():
    main()

if __name__ == "__main__":
    main()
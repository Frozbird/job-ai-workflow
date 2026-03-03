from src.data_gen.generate_jobs import run_generate
from src.pipeline_clean import run_clean
from src.pipeline_sql import run_sql
from src.pipeline_skill_analysis import run_skill
from src.pipeline_llm_report import run_llm_report

def main():
    print("=== Step 1: 生成模拟数据 ===")
    run_generate(n=1000, seed=42)

    print("\n=== Step 2: 数据清洗 ===")
    run_clean()

    print("\n=== Step 3: 写入 SQLite + SQL分析 ===")
    run_sql()

    print("\n=== Step 4: 技能词频统计 ===")
    run_skill()

    print("\n=== Step 5: 千问生成报告 ===")
    run_llm_report()

    print("\n✅ 全流程完成！请查看 report.md")

if __name__ == "__main__":
    main()
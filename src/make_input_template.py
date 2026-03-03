import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / "data" / "input" / "jobs_input.xlsx"
out.parent.mkdir(parents=True, exist_ok=True)

df = pd.DataFrame(columns=["岗位","城市","薪资","公司","学历","经验","岗位描述"])
df.to_excel(out, index=False)

print("已生成模板：", out)
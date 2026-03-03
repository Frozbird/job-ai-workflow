from pathlib import Path
import re

html_path = Path("data/raw/boss_search_auto.html")
html = html_path.read_text(encoding="utf-8", errors="ignore")

print("HTML长度:", len(html))

patterns = [
    "job-primary",
    "job-card",
    "jobName",
    "job-name",
    "salary",
    "薪资",
    "company",
    "公司",
    "__INITIAL_STATE__",
    "__NEXT_DATA__",
    "initialState",
    "window.__",
]

for p in patterns:
    cnt = len(re.findall(p, html))
    print(f"{p:18s} -> {cnt}")
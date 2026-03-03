import json
import re
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
IN_XLSX = ROOT / "data" / "processed" / "jobs_with_skills.xlsx"
OUT_DIR = ROOT / "data" / "outputs"
OUT_INDUSTRY = OUT_DIR / "industry_analysis.xlsx"
OUT_GAP = OUT_DIR / "skill_gap_analysis.xlsx"
OUT_JSON = OUT_DIR / "gap_summary.json"

# ---------- 你可以在这里维护“核心技能白名单”（混合分层规则的一部分） ----------
MANUAL_CORE = {"Python", "SQL", "Pandas", "Numpy"}

# ---------- 技能同义词映射（持续扩展） ----------
SKILL_MAP = {
    "power bi": "PowerBI",
    "powerbi": "PowerBI",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "a/b测试": "A/B测试",
    "ab测试": "A/B测试",
    "rag": "RAG",
    "prompt": "Prompt",
}

# 软技能/泛化词：不参与硬技能匹配（但可在报告里作为附加能力）
SOFT_SKILL_PATTERNS = [
    "沟通", "协调", "推动", "抗压", "责任心", "细心", "学习能力", "逻辑", "思维", "表达", "复盘", "文档",
]

def normalize_skill(s: str) -> str:
    s = str(s).strip()
    if not s:
        return ""
    key = s.lower()
    return SKILL_MAP.get(key, s)

def split_skills(skills_text: str) -> list[str]:
    if skills_text is None or (isinstance(skills_text, float) and np.isnan(skills_text)):
        return []
    text = str(skills_text).replace("，", ",")
    items = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        part = normalize_skill(part)
        items.append(part)
    # 去重保序
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return out

def is_soft_skill(skill: str) -> bool:
    return any(p in skill for p in SOFT_SKILL_PATTERNS)

def parse_salary_mid_k(salary_text: str) -> float | None:
    """
    支持：'12-24K'、'12-24K·13薪'、'20K以上'（尽量）
    返回月薪中位数（单位：K）
    """
    if salary_text is None or (isinstance(salary_text, float) and np.isnan(salary_text)):
        return None
    s = str(salary_text)
    m = re.search(r"(\d+)\s*-\s*(\d+)\s*[Kk]", s)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return (lo + hi) / 2.0
    m2 = re.search(r"(\d+)\s*[Kk]\s*以上", s)
    if m2:
        lo = int(m2.group(1))
        return float(lo)
    return None

@dataclass
class TierSets:
    core: set[str]
    extended: set[str]
    premium: set[str]

def build_skill_model(df: pd.DataFrame) -> tuple[pd.DataFrame, TierSets]:
    """
    输出：
    - skill_stats: skill, freq, freq_rate, premium_lift, weight, tier
    - tiersets: core/extended/premium 集合
    """
    # 统一技能集合（每条岗位一组）
    skills_per_job = df["skills_text"].apply(split_skills)

    # 统计频率
    all_skills = skills_per_job.explode()
    all_skills = all_skills[all_skills.notna()]
    all_skills = all_skills[all_skills.astype(str).str.len() > 0]
    all_skills = all_skills[~all_skills.astype(str).apply(is_soft_skill)]

    freq = all_skills.value_counts().rename_axis("skill").reset_index(name="freq")
    total_jobs = len(df)
    freq["freq_rate"] = freq["freq"] / max(total_jobs, 1)

    # 计算“高薪技能溢价”（Premium）：在高薪岗位中出现率 / 全体出现率
    df = df.copy()
    df["mid_k"] = df["salary_text"].apply(parse_salary_mid_k)
    q75 = df["mid_k"].dropna().quantile(0.75) if df["mid_k"].notna().any() else None

    if q75 is None:
        # 没有薪资就退化：premium_lift=1
        freq["premium_lift"] = 1.0
    else:
        is_high = df["mid_k"] >= q75
        high_skills = skills_per_job[is_high].explode()
        high_skills = high_skills[high_skills.notna()]
        high_skills = high_skills[high_skills.astype(str).str.len() > 0]
        high_skills = high_skills[~high_skills.astype(str).apply(is_soft_skill)]
        high_counts = high_skills.value_counts()

        # 高薪岗位出现率
        high_total = int(is_high.sum())
        high_rate = (high_counts / max(high_total, 1)).rename("high_rate").reset_index()
        high_rate.columns = ["skill", "high_rate"]

        freq = freq.merge(high_rate, on="skill", how="left")
        freq["high_rate"] = freq["high_rate"].fillna(0.0)

        # lift = high_rate / freq_rate（避免除0）
        freq["premium_lift"] = freq.apply(
            lambda r: (r["high_rate"] / r["freq_rate"]) if r["freq_rate"] > 0 else 1.0,
            axis=1,
        )
        # 裁剪到合理范围，避免极端值
        freq["premium_lift"] = freq["premium_lift"].clip(0.5, 3.0)

    # 权重：频率为主 + 溢价加成（可解释）
    # weight = 0.7 * freq_rate_norm + 0.3 * premium_lift_norm
    freq_rate_norm = freq["freq_rate"] / (freq["freq_rate"].max() if freq["freq_rate"].max() > 0 else 1)
    lift_norm = freq["premium_lift"] / (freq["premium_lift"].max() if freq["premium_lift"].max() > 0 else 1)
    freq["weight"] = 0.7 * freq_rate_norm + 0.3 * lift_norm

    # 分层（混合规则）
    # Core：手动核心 OR freq_rate >= 0.8
    # Extended：freq_rate 在 [0.2, 0.8) 且非 Premium
    # Premium：premium_lift >= 1.3 且 freq_rate >= 0.05（避免冷门噪声）
    freq["tier"] = "extended"
    freq.loc[(freq["skill"].isin(MANUAL_CORE)) | (freq["freq_rate"] >= 0.80), "tier"] = "core"
    freq.loc[(freq["premium_lift"] >= 1.30) & (freq["freq_rate"] >= 0.05), "tier"] = "premium"

    core_set = set(freq.loc[freq["tier"] == "core", "skill"])
    premium_set = set(freq.loc[freq["tier"] == "premium", "skill"])
    # extended = 其他（排除 core/premium）
    extended_set = set(freq["skill"]) - core_set - premium_set

    return freq.sort_values(["tier", "weight", "freq"], ascending=[True, False, False]), TierSets(
        core=core_set, extended=extended_set, premium=premium_set
    )

def weighted_match(user_skills: set[str], skill_stats: pd.DataFrame, skills_subset: set[str]) -> float:
    sub = skill_stats[skill_stats["skill"].isin(skills_subset)].copy()
    if sub.empty:
        return 0.0
    total_w = sub["weight"].sum()
    hit_w = sub[sub["skill"].isin(user_skills)]["weight"].sum()
    return float(hit_w / total_w) if total_w > 0 else 0.0

def level_from_score(score: float) -> str:
    if score < 0.30:
        return "Level 1 入门型（0-30%）"
    if score < 0.60:
        return "Level 2 成长型（30-60%）"
    if score < 0.80:
        return "Level 3 进阶型（60-80%）"
    return "Level 4 高潜型（80%+）"

def run_gap_analysis(
    user_skills_manual: str = "Excel",
    user_skills_from_resume: str = "",
    top_missing: int = 15,
):
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(IN_XLSX)
    # 兜底：列不存在也能跑
    for col in ["job_title", "city", "salary_text", "experience", "education", "company_name", "industry", "job_desc", "skills_text"]:
        if col not in df.columns:
            df[col] = ""

    # 行业分析（简版，后面你要更丰富我再加）
    df["mid_k"] = df["salary_text"].apply(parse_salary_mid_k)
    city_top = df.groupby("city", dropna=False).size().reset_index(name="job_count").sort_values("job_count", ascending=False).head(10)
    edu = df.groupby("education", dropna=False).size().reset_index(name="cnt").sort_values("cnt", ascending=False)
    exp = df.groupby("experience", dropna=False).size().reset_index(name="cnt").sort_values("cnt", ascending=False)
    city_salary = df.dropna(subset=["mid_k"]).groupby("city")["mid_k"].mean().reset_index(name="avg_mid_k").sort_values("avg_mid_k", ascending=False)

    # 技能模型
    skill_stats, tiers = build_skill_model(df)

    # 用户技能：手动 + “简历抽取结果”(先当字符串输入；下一步我们会做自动抽取)
    def parse_user_list(s: str) -> list[str]:
        if not s:
            return []
        s = str(s).replace("，", ",")
        return [normalize_skill(x.strip()) for x in s.split(",") if x.strip()]

    user_skills = set(parse_user_list(user_skills_manual) + parse_user_list(user_skills_from_resume))
    # 过滤软技能
    user_skills = {s for s in user_skills if s and (not is_soft_skill(s))}

    core_score = weighted_match(user_skills, skill_stats, tiers.core)
    ext_score = weighted_match(user_skills, skill_stats, tiers.extended)
    prem_score = weighted_match(user_skills, skill_stats, tiers.premium)

    overall = 0.5 * core_score + 0.3 * ext_score + 0.2 * prem_score
    level = level_from_score(overall)

    # 缺失技能：按权重排序，优先缺失的“核心+高薪”
    wanted = skill_stats.copy()
    wanted["is_missing"] = ~wanted["skill"].isin(user_skills)
    missing = wanted[wanted["is_missing"]].sort_values(["tier", "weight", "freq"], ascending=[True, False, False]).head(top_missing)

    # 输出 Excel：industry_analysis.xlsx
    with pd.ExcelWriter(OUT_INDUSTRY, engine="openpyxl") as w:
        city_top.to_excel(w, sheet_name="城市岗位Top10", index=False)
        city_salary.to_excel(w, sheet_name="城市平均月薪K", index=False)
        edu.to_excel(w, sheet_name="学历分布", index=False)
        exp.to_excel(w, sheet_name="经验分布", index=False)
        skill_stats.head(50).to_excel(w, sheet_name="技能Top50", index=False)

    # 输出 Excel：skill_gap_analysis.xlsx
    summary = pd.DataFrame([{
        "user_skills": ",".join(sorted(user_skills)),
        "core_match": round(core_score, 4),
        "extended_match": round(ext_score, 4),
        "premium_match": round(prem_score, 4),
        "overall_match": round(overall, 4),
        "level": level,
    }])

    with pd.ExcelWriter(OUT_GAP, engine="openpyxl") as w:
        summary.to_excel(w, sheet_name="匹配度总览", index=False)
        missing.to_excel(w, sheet_name="缺失技能Top", index=False)

    # 输出 JSON（给 LLM 用）
    payload = {
        "overall_match": overall,
        "level": level,
        "core_match": core_score,
        "extended_match": ext_score,
        "premium_match": prem_score,
        "user_skills": sorted(list(user_skills)),
        "top_missing": missing[["skill", "tier", "weight", "freq"]].to_dict(orient="records"),
        "city_top10": city_top.to_dict(orient="records"),
        "city_salary": city_salary.head(10).to_dict(orient="records"),
        "edu_dist": edu.to_dict(orient="records"),
        "exp_dist": exp.to_dict(orient="records"),
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("✅ 已输出行业分析：", OUT_INDUSTRY)
    print("✅ 已输出能力差距：", OUT_GAP)
    print("✅ 已输出结构化摘要：", OUT_JSON)
    print("综合匹配度：", round(overall * 100, 1), "% |", level)

if __name__ == "__main__":
    # 先用最小输入跑通：你可以把 Excel/SQL/Python 等改成你的真实技能
    run_gap_analysis(user_skills_manual="Excel,Python", user_skills_from_resume="")
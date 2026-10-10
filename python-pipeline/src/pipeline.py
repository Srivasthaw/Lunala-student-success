"""Load -> clean -> integrate -> score -> flag risk -> segment.

Run:  python -m src.pipeline
Produces data/processed/*.csv which the dashboard reads.
"""
import os

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from . import config as C

SOURCES = ["academic", "attendance", "lms", "engagement", "placement", "skills", "feedback", "psychometrics"]


# ----------------------------------------------------------------------------
# 1. LOAD
# ----------------------------------------------------------------------------
def load_raw(raw_dir=C.RAW_DIR):
    return {s: pd.read_csv(f"{raw_dir}/{s}.csv") for s in SOURCES}


# ----------------------------------------------------------------------------
# 2. CLEAN  (every fix is written to a log so you can show it in the demo)
# ----------------------------------------------------------------------------
def clean(raw):
    log = []

    def note(source, issue, action, count):
        log.append({"source": source, "issue": issue, "action": action, "rows_affected": int(count)})

    d = {k: v.copy() for k, v in raw.items()}

    # duplicates
    for name, df in d.items():
        dups = df.duplicated(subset="student_id").sum()
        if dups:
            d[name] = df.drop_duplicates(subset="student_id", keep="first").copy()
            note(name, "Duplicate student_id rows", "Kept first occurrence", dups)

    # impossible percentages
    for col in ["overall_pct", "maths_pct", "programming_pct", "core_subject_pct"]:
        n = (d["attendance"][col] > 100).sum()
        if n:
            d["attendance"][col] = d["attendance"][col].clip(upper=100)
            note("attendance", f"{col} above 100", "Capped at 100", n)

    # psychometric scales are 0-100
    for col in C.PSY_COLS:
        n = (d["psychometrics"][col] > 100).sum()
        if n:
            d["psychometrics"][col] = d["psychometrics"][col].clip(upper=100)
            note("psychometrics", f"{col} above 100", "Capped at 100", n)

    # inconsistent text labels
    ts = d["skills"]["technical_skill"]
    fixed = ts.str.strip().str.title()
    n = (ts != fixed).sum()
    d["skills"]["technical_skill"] = fixed
    if n:
        note("skills", "Inconsistent case/spaces in technical_skill", "Stripped and title-cased", n)

    # missing numeric values -> median of that column (simple, explainable choice)
    for name, df in d.items():
        for col in df.select_dtypes("number").columns:
            n = df[col].isna().sum()
            if n:
                df[col] = df[col].fillna(df[col].median())
                note(name, f"Missing {col}", "Filled with column median", n)
    return d, log


# ----------------------------------------------------------------------------
# 3. INTEGRATE  (one row per student = "unified student view")
# ----------------------------------------------------------------------------
def integrate(d, log):
    df = d["academic"]
    for name in SOURCES[1:]:
        before = len(df)
        df = df.merge(d[name], on="student_id", how="left")
        assert len(df) == before, f"Merge with {name} changed row count"

    # students absent from a source (e.g. feedback) -> neutral median, and logged
    missing_fb = int(df["satisfaction"].isna().sum())
    for col in ["satisfaction", "faculty_feedback"]:
        df[col] = df[col].fillna(df[col].median())
    if missing_fb:
        log.append({"source": "feedback", "issue": "Students missing from source",
                    "action": "Used median feedback (neutral)", "rows_affected": missing_fb})
    return df


# ----------------------------------------------------------------------------
# 4. SCORE
# ----------------------------------------------------------------------------
def indicator_scores(df):
    """Turn raw columns into six 0-100 indicator scores."""
    s = pd.DataFrame(index=df.index)
    cgpa_score = df["cgpa"] * 10
    backlog_score = (100 - df["backlogs"] * 25).clip(lower=0)
    s["Academic"] = 0.7 * cgpa_score + 0.3 * backlog_score
    s["Attendance"] = df["overall_pct"]
    s["LMS"] = 0.4 * (df["logins_per_week"] / 10).clip(upper=1) * 100 + 0.6 * df["assignment_completion_pct"]
    s["Engagement"] = (df["events"] * 8 + df["clubs"] * 10
                       + df["hackathons"] * 15 + df["certifications"] * 12).clip(upper=100)
    tech = df["technical_skill"].map({"Beginner": 30, "Intermediate": 60, "Advanced": 90}).fillna(30)
    skills = 0.6 * tech + 0.4 * df["soft_skill_score"]
    tests = df[["aptitude", "coding", "mock_interview"]].mean(axis=1)
    s["Placement"] = 0.7 * tests + 0.3 * skills
    s["Feedback"] = (df["satisfaction"] + df["faculty_feedback"]) / 2 / 5 * 100
    # Psychometrics: average of 4 positive traits and (100 - stress)
    pos = df[["conscientiousness", "emotional_stability", "grit", "motivation"]].sum(axis=1)
    s["Psychometrics"] = (pos + (100 - df["stress_level"])) / 5
    return s.clip(0, 100).round(1)


def score(df):
    ind = indicator_scores(df)
    out = df.copy()
    for k, w in C.WEIGHTS.items():
        out[f"score_{k}"] = ind[k]
        out[f"points_{k}"] = (ind[k] * w).round(2)   # contribution to the final score
    out["success_score"] = sum(ind[k] * w for k, w in C.WEIGHTS.items()).round(1)
    # biggest drag = indicator that lost the most points vs its maximum
    lost = pd.DataFrame({k: (100 - ind[k]) * w for k, w in C.WEIGHTS.items()})
    out["biggest_drag"] = lost.idxmax(axis=1)
    out["risk_band"] = pd.cut(out["success_score"], [-1, C.HIGH_RISK_BELOW, C.MEDIUM_RISK_BELOW, 101],
                              labels=["High", "Medium", "Low"], right=False).astype(str)
    return out


# ----------------------------------------------------------------------------
# 5. RISK FLAGS (rule based, with human-readable reasons)
# ----------------------------------------------------------------------------
def flag_risk(df):
    def apply(rules):
        hits = pd.DataFrame({name: rule(df) for name, rule in rules.items()})
        return hits.any(axis=1), hits.apply(lambda r: "; ".join(r.index[r]), axis=1)

    df["academic_risk"], df["academic_reasons"] = apply(C.ACADEMIC_RULES)
    df["placement_risk"], df["placement_reasons"] = apply(C.PLACEMENT_RULES)
    df["psychometric_risk"], df["psychometric_reasons"] = apply(C.PSYCHOMETRIC_RULES)
    df["any_risk"] = df["academic_risk"] | df["placement_risk"] | df["psychometric_risk"]
    return df


# ----------------------------------------------------------------------------
# 6. SEGMENT (KMeans on the six indicator scores, then name each cluster)
# ----------------------------------------------------------------------------
ACTIONS = {
    "Top performers": "Mentor others; fast-track for internships and leadership roles.",
    "High academics, low placement readiness": "Targeted aptitude, coding and mock-interview training.",
    "At-risk, needs urgent support": "Faculty mentor, attendance follow-up, remedial classes.",
    "Disengaged but capable": "Counselling and engagement drives: clubs, hackathons, peer groups.",
    "Steady middle": "Light-touch nudges; encourage certifications and activities.",
}


def segment(df):
    cols = [f"score_{k}" for k in C.WEIGHTS]
    X = StandardScaler().fit_transform(df[cols])
    km = KMeans(n_clusters=C.N_SEGMENTS, n_init=10, random_state=C.RANDOM_SEED).fit(X)
    df["cluster"] = km.labels_

    cen = df.groupby("cluster")[[*cols, "success_score"]].mean()
    mean = df[cols].mean()
    q75, q25 = df["success_score"].quantile(0.75), df["success_score"].quantile(0.25)
    habit_mean = mean["score_Engagement"] + mean["score_LMS"] + mean["score_Attendance"]

    names = {}
    for c, r in cen.iterrows():
        habits = r["score_Engagement"] + r["score_LMS"] + r["score_Attendance"]
        if r["success_score"] >= q75:
            n = "Top performers"
        elif r["score_Academic"] > mean["score_Academic"] and r["score_Placement"] < mean["score_Placement"] - 3:
            n = "High academics, low placement readiness"
        elif r["success_score"] <= q25:
            n = "At-risk, needs urgent support"
        elif habits < habit_mean - 5:
            n = "Disengaged but capable"
        else:
            n = "Steady middle"
        names[c] = n

    # make names unique if two clusters got the same label
    seen = {}
    for c in sorted(names):
        base = names[c]
        seen[base] = seen.get(base, 0) + 1
        if seen[base] > 1:
            names[c] = f"{base} ({seen[base]})"

    df["segment"] = df["cluster"].map(names)
    df["suggested_action"] = df["segment"].map(lambda s: ACTIONS.get(s.split(" (")[0], ""))
    return df


# ----------------------------------------------------------------------------
def run():
    raw = load_raw()
    d, log = clean(raw)
    df = integrate(d, log)
    df = score(df)
    df = flag_risk(df)
    df = segment(df)

    os.makedirs(os.path.dirname(C.PROCESSED_PATH), exist_ok=True)
    df.to_csv(C.PROCESSED_PATH, index=False)
    pd.DataFrame(log).to_csv(C.QUALITY_LOG_PATH, index=False)
    summary = (df.groupby("segment")
                 .agg(students=("student_id", "count"), avg_score=("success_score", "mean"),
                      avg_academic=("score_Academic", "mean"), avg_placement=("score_Placement", "mean"),
                      pct_any_risk=("any_risk", "mean"), action=("suggested_action", "first"))
                 .round(2).reset_index())
    summary.to_csv(C.SEGMENT_SUMMARY_PATH, index=False)

    print(f"Processed {len(df)} students. Risk bands:\n{df['risk_band'].value_counts().to_string()}")
    print(f"Cleaning actions logged: {len(log)}")
    return df


if __name__ == "__main__":
    run()

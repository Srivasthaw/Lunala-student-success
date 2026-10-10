"""Turn the processed data into plain-English findings for the dashboard and slides."""
import pandas as pd


def pct(x):
    return f"{x * 100:.0f}%"


def generate_insights(df: pd.DataFrame) -> list[str]:
    out = []

    # 1. attendance vs risk
    low, ok = df[df["overall_pct"] < 60], df[df["overall_pct"] >= 75]
    if len(low) and len(ok):
        out.append(
            f"Students with attendance below 60% have an average Success Score of "
            f"{low['success_score'].mean():.0f}, versus {ok['success_score'].mean():.0f} for those at 75% or above "
            f"({len(low)} students are in the low group)."
        )

    # 2. academic vs placement gap
    gap = df[(df["score_Academic"] >= 75) & (df["score_Placement"] < 55)]
    if len(gap):
        out.append(
            f"{len(gap)} students ({pct(len(gap) / len(df))}) have strong academics (75+) but weak placement "
            f"readiness (below 55). They are the best target for aptitude and mock-interview training."
        )

    # 3. engagement lifts placement
    eng_hi = df[df["score_Engagement"] >= df["score_Engagement"].quantile(0.75)]
    eng_lo = df[df["score_Engagement"] <= df["score_Engagement"].quantile(0.25)]
    out.append(
        f"Highly engaged students (top 25% in clubs, events, hackathons) average {eng_hi['score_Placement'].mean():.0f} "
        f"placement readiness against {eng_lo['score_Placement'].mean():.0f} for the least engaged."
    )

    # 3b. psychometrics
    hi, lo = df[df["stress_level"] > 65], df[df["stress_level"] < 40]
    if len(hi) and len(lo):
        out.append(
            f"{len(hi)} students report high stress (above 65). They average {hi['backlogs'].mean():.1f} backlogs "
            f"versus {lo['backlogs'].mean():.1f} for low-stress students, so backlog support and early "
            f"counselling may go together."
        )
    cons = df.sort_values("conscientiousness")
    q = len(df) // 4
    out.append(
        f"The most conscientious quarter averages a Success Score of {cons['success_score'].tail(q).mean():.0f} "
        f"versus {cons['success_score'].head(q).mean():.0f} for the least conscientious."
    )

    # 4. department with most risk
    dept = df.groupby("department")["any_risk"].mean().sort_values(ascending=False)
    out.append(
        f"{dept.index[0]} has the highest share of at-risk students ({pct(dept.iloc[0])}), "
        f"while {dept.index[-1]} has the lowest ({pct(dept.iloc[-1])})."
    )

    # 5. most common driver
    drag = df[df["risk_band"] == "High"]["biggest_drag"].value_counts()
    if len(drag):
        out.append(
            f"Among High-risk students, the most common biggest drag on the score is "
            f"{drag.index[0]} ({pct(drag.iloc[0] / drag.sum())} of them)."
        )

    # 6. backlogs
    b = df.groupby(df["backlogs"] >= 3)["overall_pct"].mean()
    if True in b.index and False in b.index:
        out.append(
            f"Students with 3 or more backlogs average {b[True]:.0f}% attendance, versus {b[False]:.0f}% for others."
        )
    return out

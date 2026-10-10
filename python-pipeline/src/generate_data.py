"""Create realistic FAKE college data as 8 separate CSV files (one per source system).

Run:  python -m src.generate_data

Hidden patterns are planted on purpose so your analysis finds real insights:
  * Low attendance goes with low CGPA and more backlogs.
  * Some students have strong academics but weak placement skills.
  * Engagement (clubs, hackathons) lifts coding and mock-interview scores.
  * Conscientiousness, grit and motivation follow effort; stress rises with backlogs.
The files are also deliberately MESSY (nulls, duplicates, impossible values,
inconsistent labels, missing rows) so the cleaning step has real work to do.
"""
import os

import numpy as np
import pandas as pd

from .config import RAW_DIR, RANDOM_SEED

N = 500
DEPTS = ["CSE", "IT", "ECE", "Mechanical", "Civil"]


def clip(x, lo, hi):
    return np.clip(x, lo, hi)


def generate(n=N, seed=RANDOM_SEED, out_dir=RAW_DIR):
    rng = np.random.default_rng(seed)
    ids = [f"S{1000 + i}" for i in range(n)]

    ability = rng.normal(0, 1, n)      # hidden: academic ability
    effort = rng.normal(0, 1, n)       # hidden: effort / discipline
    practical = rng.normal(0, 1, n)    # hidden: practical / placement skill

    dept = rng.choice(DEPTS, n, p=[0.3, 0.2, 0.2, 0.15, 0.15])
    sem = rng.integers(1, 9, n)

    # ---- Academic
    cgpa = clip(6.8 + 1.0 * ability + 0.5 * effort + rng.normal(0, 0.4, n), 3.0, 10.0)
    backlogs = np.where(cgpa < 6.5, rng.poisson(2.2, n), rng.poisson(0.2, n))
    academic = pd.DataFrame({
        "student_id": ids,
        "name": [f"Student {i}" for i in range(n)],
        "department": dept,
        "semester": sem,
        "cgpa": cgpa.round(2),
        "backlogs": backlogs,
        "avg_marks": clip(cgpa * 10 + rng.normal(0, 4, n), 20, 100).round(1),
    })

    # ---- Attendance (driven by effort)
    att = clip(76 + 12 * effort + 3 * ability + rng.normal(0, 6, n), 25, 100)
    attendance = pd.DataFrame({
        "student_id": ids,
        "overall_pct": att.round(1),
        "maths_pct": clip(att + rng.normal(0, 6, n), 0, 100).round(1),
        "programming_pct": clip(att + rng.normal(0, 6, n), 0, 100).round(1),
        "core_subject_pct": clip(att + rng.normal(0, 6, n), 0, 100).round(1),
    })

    # ---- LMS activity
    lms = pd.DataFrame({
        "student_id": ids,
        "logins_per_week": clip(5 + 2.5 * effort + rng.normal(0, 1.5, n), 0, 20).round(1),
        "assignment_completion_pct": clip(70 + 14 * effort + 4 * ability + rng.normal(0, 8, n), 0, 100).round(1),
    })

    # ---- Engagement
    eng_base = np.clip(1.5 + 0.9 * effort + 0.5 * practical, 0.1, None)
    engagement = pd.DataFrame({
        "student_id": ids,
        "events": rng.poisson(eng_base * 1.5),
        "clubs": rng.poisson(eng_base * 0.5),
        "hackathons": rng.poisson(eng_base * 0.35),
        "certifications": rng.poisson(eng_base * 0.7),
    })
    eng_boost = 4 * (engagement["hackathons"] + engagement["clubs"]).to_numpy()

    # ---- Placement readiness (some strong-academic students are weak here)
    gap = (rng.random(n) < 0.18) & (ability > 0.3)
    pr = 55 + 14 * practical + 6 * ability + eng_boost
    pr = np.where(gap, pr - 28, pr)
    placement = pd.DataFrame({
        "student_id": ids,
        "aptitude": clip(pr + rng.normal(0, 8, n), 0, 100).round(1),
        "coding": clip(pr + 5 * (dept == "CSE") + rng.normal(0, 10, n), 0, 100).round(1),
        "mock_interview": clip(pr - 3 + rng.normal(0, 10, n), 0, 100).round(1),
    })

    # ---- Skills
    tech = clip(pr + rng.normal(0, 8, n), 0, 100)
    labels = np.select([tech < 40, tech < 70], ["Beginner", "Intermediate"], "Advanced")
    skills = pd.DataFrame({
        "student_id": ids,
        "technical_skill": labels,
        "soft_skill_score": clip(60 + 8 * practical + 4 * effort + rng.normal(0, 10, n), 0, 100).round(1),
    })

    # ---- Feedback
    feedback = pd.DataFrame({
        "student_id": ids,
        "satisfaction": clip(np.round(3.4 + 0.4 * effort + rng.normal(0, 0.8, n)), 1, 5).astype(int),
        "faculty_feedback": clip(np.round(3.3 + 0.5 * effort + 0.3 * ability + rng.normal(0, 0.8, n)), 1, 5).astype(int),
    })

    # ---- Psychometrics (self-reported traits, 0-100; stress is higher = worse)
    stab = rng.normal(0, 1, n)         # hidden: emotional stability
    psychometrics = pd.DataFrame({
        "student_id": ids,
        "conscientiousness": clip(55 + 14 * effort + rng.normal(0, 9, n), 0, 100).round(1),
        "openness": clip(58 + 8 * ability + rng.normal(0, 12, n), 0, 100).round(1),
        "extraversion": clip(52 + 8 * practical + rng.normal(0, 14, n), 0, 100).round(1),
        "agreeableness": clip(62 + rng.normal(0, 12, n), 0, 100).round(1),
        "emotional_stability": clip(58 + 13 * stab + rng.normal(0, 8, n), 0, 100).round(1),
        "grit": clip(55 + 12 * effort + 5 * ability + rng.normal(0, 9, n), 0, 100).round(1),
        "motivation": clip(60 + 11 * effort + 6 * practical + rng.normal(0, 9, n), 0, 100).round(1),
        "stress_level": clip(48 - 12 * stab + 4 * np.minimum(backlogs, 4) + rng.normal(0, 9, n), 0, 100).round(1),
    })

    # ======= Make it MESSY on purpose =======
    def blank(df, col, frac):
        idx = rng.choice(df.index, int(len(df) * frac), replace=False)
        df.loc[idx, col] = np.nan

    blank(academic, "cgpa", 0.02)
    blank(placement, "mock_interview", 0.06)
    blank(engagement, "events", 0.04)
    blank(lms, "assignment_completion_pct", 0.03)
    blank(psychometrics, "stress_level", 0.04)
    psychometrics.loc[rng.choice(psychometrics.index, 5, replace=False), "grit"] = 105  # impossible

    # impossible values
    bad = rng.choice(attendance.index, 6, replace=False)
    attendance.loc[bad, "overall_pct"] = [105, 110, 120, 101, 150, 103]

    # duplicate rows in LMS
    lms = pd.concat([lms, lms.sample(12, random_state=seed)], ignore_index=True)

    # inconsistent text labels
    messy = rng.choice(skills.index, 40, replace=False)
    skills.loc[messy[:20], "technical_skill"] = skills.loc[messy[:20], "technical_skill"].str.lower()
    skills.loc[messy[20:], "technical_skill"] = " " + skills.loc[messy[20:], "technical_skill"].str.upper() + " "

    # students missing from feedback
    feedback = feedback.drop(feedback.sample(30, random_state=seed).index)

    os.makedirs(out_dir, exist_ok=True)
    files = dict(academic=academic, attendance=attendance, lms=lms, engagement=engagement,
                 placement=placement, skills=skills, feedback=feedback, psychometrics=psychometrics)
    for name, df in files.items():
        df.to_csv(f"{out_dir}/{name}.csv", index=False)
    print(f"Wrote {len(files)} raw files to {out_dir}/ for {n} students.")


if __name__ == "__main__":
    generate()

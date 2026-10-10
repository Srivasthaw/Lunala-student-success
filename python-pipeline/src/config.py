"""All tunable settings live here. Change a number, re-run the pipeline, see the effect."""

# --- Student Success Score: weights (must add up to 1.0) -------------------
WEIGHTS = {
    "Academic": 0.30,
    "Attendance": 0.20,
    "LMS": 0.10,
    "Engagement": 0.10,
    "Placement": 0.15,
    "Feedback": 0.05,
    "Psychometrics": 0.10,
}

# Psychometric columns (0-100 scales). Big Five + grit, motivation, stress.
# Only 5 of these feed the score; openness, extraversion and agreeableness are
# descriptive (shown in the dashboard) because they do not clearly predict success.
PSY_COLS = ["conscientiousness", "openness", "extraversion", "agreeableness",
            "emotional_stability", "grit", "motivation", "stress_level"]

# --- Overall risk bands (based on Success Score 0-100) ---------------------
HIGH_RISK_BELOW = 50
MEDIUM_RISK_BELOW = 70

# --- Rule-based flags (each triggered rule is shown as a "reason") ---------
ACADEMIC_RULES = {
    "CGPA below 6.0": lambda d: d["cgpa"] < 6.0,
    "Attendance below 60%": lambda d: d["overall_pct"] < 60,
    "3 or more backlogs": lambda d: d["backlogs"] >= 3,
}
PLACEMENT_RULES = {
    "Placement test average below 45": lambda d: d[["aptitude", "coding", "mock_interview"]].mean(axis=1) < 45,
    "Coding score below 35": lambda d: d["coding"] < 35,
    "Mock interview below 35": lambda d: d["mock_interview"] < 35,
}

PSYCHOMETRIC_RULES = {
    "Stress level above 75": lambda d: d["stress_level"] > 75,
    "Emotional stability below 35": lambda d: d["emotional_stability"] < 35,
    "Grit below 35": lambda d: d["grit"] < 35,
}

# --- Segmentation -----------------------------------------------------------
N_SEGMENTS = 4
RANDOM_SEED = 42

# --- Paths (run all commands from the project root folder) ------------------
RAW_DIR = "data/raw"
PROCESSED_PATH = "data/processed/student_scores.csv"
SEGMENT_SUMMARY_PATH = "data/processed/segment_summary.csv"
QUALITY_LOG_PATH = "data/processed/data_quality_log.csv"

"""Quick sanity checks. Run:  python tests_smoke.py"""
import pandas as pd
from src import config as C
from src.generate_data import generate
from src.pipeline import run

assert abs(sum(C.WEIGHTS.values()) - 1) < 1e-9, "Weights must add to 1"
generate()
df = run()
assert df["student_id"].is_unique, "Duplicate students after merge"
assert len(df) == 500
assert df["success_score"].between(0, 100).all()
assert set(df["risk_band"]) <= {"High", "Medium", "Low"}
assert df[[f"score_{k}" for k in C.WEIGHTS]].notna().all().all()
recon = sum(df[f"points_{k}"] for k in C.WEIGHTS)
assert (recon - df["success_score"]).abs().max() < 0.2, "Points should add up to the score"
assert df["psychometric_risk"].dtype == bool
assert df["grit"].max() <= 100, "Psychometric values should be capped at 100"
print("All checks passed.")

# Student Success Platform

An analytics and AI-assisted platform that merges eight college data sources (including psychometrics) into one student view, computes an explainable **Student Success Score**, flags at-risk students, groups them into segments, and shows everything in an interactive Streamlit dashboard.

Built for KPMG in India, Challenge 04 (Smart Campus Analytics). **All data is synthetic.**

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m src.generate_data      # 1. create 8 messy raw CSVs in data/raw/
python -m src.pipeline           # 2. clean, merge, score, flag, segment -> data/processed/
streamlit run app.py             # 3. open the dashboard
python tests_smoke.py            # optional sanity checks
```

## How it works
```
data/raw/*.csv  ->  clean  ->  integrate  ->  score  ->  risk flags  ->  segments  ->  data/processed/  ->  app.py
 (8 sources)       (logged)   (student_id)   (6 weights)  (rules+reasons)  (KMeans)
```

| File | What it does |
|---|---|
| `src/config.py` | Weights, risk thresholds, rules, paths. **Start here to tune the model.** |
| `src/generate_data.py` | Fake data with planted patterns and deliberate mess |
| `src/pipeline.py` | Cleaning, merge, scoring, flags, segmentation |
| `src/insights.py` | Auto-written findings shown in the dashboard |
| `app.py` | Streamlit dashboard (6 tabs) |
| `docs/score_note.md` | Deliverable: explanation of the score |

## Dashboard tabs
Overview, At-risk students (downloadable), Student detail (explainable score, radar, psychometric profile), Segments, Psychometrics, Insights, Data quality log.

## Ideas to extend (your turn)
- Replace synthetic data with a real or public dataset; map its columns in `pipeline.py`.
- Add a predictive model (logistic regression or random forest) for placement outcome and compare it with the rule-based score.
- Use SHAP values for model-based explanations.
- Add semester-over-semester trends per student and early-warning alerts.
- Add an LLM assistant that answers questions over the processed data and drafts intervention emails.
- Add login roles (faculty vs admin), Docker, and CI that runs `tests_smoke.py`.

## Deliverables checklist
- [x] Working dashboard prototype (`app.py`)
- [x] Score note (`docs/score_note.md`)
- [ ] 5-6 slides or a short demo recording (your turn)

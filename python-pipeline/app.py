"""Student Success Dashboard.   Run:  streamlit run app.py"""
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src import config as C
from src.insights import generate_insights

st.set_page_config(page_title="Student Success Platform", page_icon="🎓", layout="wide")

RISK_COLORS = {"High": "#d62839", "Medium": "#e09f00", "Low": "#2b9348"}
INDICATORS = list(C.WEIGHTS)


@st.cache_data
def load():
    if not os.path.exists(C.PROCESSED_PATH):
        return None, None, None
    df = pd.read_csv(C.PROCESSED_PATH).fillna({"academic_reasons": "", "placement_reasons": ""})
    seg = pd.read_csv(C.SEGMENT_SUMMARY_PATH)
    log = pd.read_csv(C.QUALITY_LOG_PATH)
    return df, seg, log


df, seg, log = load()
if df is None:
    st.error("No processed data found. Run these two commands first:\n\n"
             "`python -m src.generate_data` then `python -m src.pipeline`")
    st.stop()

# ----------------------------------------------------------------- sidebar filters
st.sidebar.title("🎓 Filters")
depts = st.sidebar.multiselect("Department", sorted(df["department"].unique()), default=sorted(df["department"].unique()))
sems = st.sidebar.multiselect("Semester", sorted(df["semester"].unique()), default=sorted(df["semester"].unique()))
bands = st.sidebar.multiselect("Risk band", ["High", "Medium", "Low"], default=["High", "Medium", "Low"])
f = df[df["department"].isin(depts) & df["semester"].isin(sems) & df["risk_band"].isin(bands)]
st.sidebar.caption(f"{len(f)} of {len(df)} students shown")
st.sidebar.markdown("---")
st.sidebar.caption("Weights are set in `src/config.py`. Change them, re-run the pipeline, refresh.")

st.title("Student Success Platform")
st.caption("Unified view of academics, attendance, LMS, engagement, placement, skills and feedback.")

if f.empty:
    st.warning("No students match these filters.")
    st.stop()

# ----------------------------------------------------------------- KPIs
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Students", len(f))
k2.metric("Avg Success Score", f"{f['success_score'].mean():.1f}")
k3.metric("High risk", int((f["risk_band"] == "High").sum()))
k4.metric("Academic risk flags", int(f["academic_risk"].sum()))
k5.metric("Placement risk flags", int(f["placement_risk"].sum()))
k6.metric("Wellbeing flags", int(f["psychometric_risk"].sum()))

tab_over, tab_risk, tab_student, tab_seg, tab_psy, tab_ins, tab_data = st.tabs(
    ["📊 Overview", "🚨 At-risk students", "🔍 Student detail", "🧩 Segments", "🧠 Psychometrics", "💡 Insights", "🧹 Data quality"])
TRAITS = C.PSY_COLS

# ----------------------------------------------------------------- Overview
with tab_over:
    c1, c2 = st.columns(2)
    fig = px.histogram(f, x="success_score", color="risk_band", nbins=25, color_discrete_map=RISK_COLORS,
                       title="Success Score distribution", labels={"success_score": "Success Score"})
    c1.plotly_chart(fig, use_container_width=True)

    dept = f.groupby("department").agg(avg_score=("success_score", "mean"), at_risk=("any_risk", "mean")).reset_index()
    fig = px.bar(dept, x="department", y="avg_score", color="at_risk", color_continuous_scale="RdYlGn_r",
                 title="Average score by department (colour = share at risk)", labels={"avg_score": "Avg score", "at_risk": "Share at risk"})
    c2.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    fig = px.scatter(f, x="overall_pct", y="success_score", color="risk_band", color_discrete_map=RISK_COLORS,
                     hover_data=["student_id", "department"], title="Attendance vs Success Score",
                     labels={"overall_pct": "Attendance %", "success_score": "Success Score"})
    c3.plotly_chart(fig, use_container_width=True)

    sem = f.groupby("semester").agg(avg_score=("success_score", "mean"), high=("risk_band", lambda s: (s == "High").mean())).reset_index()
    fig = px.line(sem, x="semester", y="avg_score", markers=True, title="Average score by semester (trend)")
    c4.plotly_chart(fig, use_container_width=True)

    avg = f[[f"score_{k}" for k in INDICATORS]].mean()
    fig = px.bar(x=INDICATORS, y=avg.values, title="Average indicator score (where is the cohort weak?)",
                 labels={"x": "Indicator", "y": "Avg 0-100"})
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------- At risk
with tab_risk:
    st.subheader("Students who may need intervention")
    kind = st.radio("Show", ["Any risk flag", "Academic risk", "Placement risk", "Wellbeing risk", "High risk band"], horizontal=True)
    mask = {"Any risk flag": f["any_risk"], "Academic risk": f["academic_risk"],
            "Placement risk": f["placement_risk"], "Wellbeing risk": f["psychometric_risk"], "High risk band": f["risk_band"] == "High"}[kind]
    r = f[mask].sort_values("success_score")
    st.write(f"**{len(r)} students**, lowest score first.")
    show = r[["student_id", "name", "department", "semester", "success_score", "risk_band",
              "biggest_drag", "academic_reasons", "placement_reasons", "psychometric_reasons", "segment", "suggested_action"]]
    st.dataframe(show, use_container_width=True, hide_index=True)
    st.download_button("⬇ Download this list (CSV)", show.to_csv(index=False), "at_risk_students.csv", "text/csv")

# ----------------------------------------------------------------- Student detail
with tab_student:
    options = f.sort_values("success_score")["student_id"] + " · " + f.sort_values("success_score")["name"]
    pick = st.selectbox("Choose a student (lowest scores first)", options)
    s = f[f["student_id"] == pick.split(" · ")[0]].iloc[0]

    a, b, c = st.columns(3)
    a.metric("Success Score", f"{s['success_score']:.1f}")
    b.metric("Risk band", s["risk_band"])
    c.metric("Segment", s["segment"])

    left, right = st.columns(2)
    # explainable score: points earned vs maximum possible per indicator
    pts = pd.DataFrame({"Indicator": INDICATORS,
                        "Earned": [s[f"points_{k}"] for k in INDICATORS],
                        "Max": [C.WEIGHTS[k] * 100 for k in INDICATORS]})
    pts["Lost"] = pts["Max"] - pts["Earned"]
    fig = go.Figure()
    fig.add_bar(x=pts["Indicator"], y=pts["Earned"], name="Points earned", marker_color="#2b9348")
    fig.add_bar(x=pts["Indicator"], y=pts["Lost"], name="Points lost", marker_color="#d6283955")
    fig.update_layout(barmode="stack", title="Why this score? (points earned vs lost per indicator)")
    left.plotly_chart(fig, use_container_width=True)

    vals = [s[f"score_{k}"] for k in INDICATORS]
    avgs = [df[f"score_{k}"].mean() for k in INDICATORS]
    radar = go.Figure()
    radar.add_trace(go.Scatterpolar(r=vals + vals[:1], theta=INDICATORS + INDICATORS[:1], fill="toself", name="Student"))
    radar.add_trace(go.Scatterpolar(r=avgs + avgs[:1], theta=INDICATORS + INDICATORS[:1], name="College average"))
    radar.update_layout(polar=dict(radialaxis=dict(range=[0, 100])), title="Profile vs college average")
    right.plotly_chart(radar, use_container_width=True)

    st.markdown(f"**Biggest drag on the score:** {s['biggest_drag']}")
    st.markdown(f"**Academic flags:** {s['academic_reasons'] or 'None'}")
    st.markdown(f"**Placement flags:** {s['placement_reasons'] or 'None'}")
    st.markdown(f"**Wellbeing flags:** {s['psychometric_reasons'] or 'None'}")
    tr = pd.DataFrame({"Trait": [t.replace("_", " ") for t in TRAITS],
                       "Student": [s[t] for t in TRAITS], "College average": [df[t].mean() for t in TRAITS]})
    fig = px.bar(tr, x="Trait", y=["Student", "College average"], barmode="group", title="Psychometric profile")
    st.plotly_chart(fig, use_container_width=True)
    st.info(f"**Suggested action:** {s['suggested_action']}")

# ----------------------------------------------------------------- Segments
with tab_seg:
    st.subheader("Student segments (KMeans clustering)")
    fig = px.scatter(f, x="score_Academic", y="score_Placement", color="segment", hover_data=["student_id", "success_score"],
                     title="Academic strength vs placement readiness",
                     labels={"score_Academic": "Academic score", "score_Placement": "Placement score"})
    fig.add_hline(y=55, line_dash="dot")
    fig.add_vline(x=75, line_dash="dot")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(seg.rename(columns={"pct_any_risk": "share_with_risk_flag"}), use_container_width=True, hide_index=True)

# ----------------------------------------------------------------- Psychometrics
with tab_psy:
    st.subheader("Psychometric profile")
    st.info("Scores are self-reported. Use them to guide supportive conversations (counselling, mentoring), "
            "never to label, rank or exclude students. Collect real data only with consent.")
    avg_t = f[TRAITS].mean().round(1)
    c1, c2 = st.columns(2)
    fig = px.bar(x=avg_t.values, y=[t.replace("_", " ") for t in avg_t.index], orientation="h",
                 title="Average profile (stress: higher is worse)", labels={"x": "Average (0-100)", "y": ""})
    c1.plotly_chart(fig, use_container_width=True)
    corr = f[TRAITS + ["overall_pct", "cgpa", "success_score"]].corr()["success_score"].drop("success_score")
    corr = corr.sort_values()
    fig = px.bar(x=corr.values, y=[t.replace("_", " ") for t in corr.index], orientation="h",
                 title="Correlation with Success Score", labels={"x": "Correlation", "y": ""})
    c2.plotly_chart(fig, use_container_width=True)
    fig = px.scatter(f, x="conscientiousness", y="success_score", color="risk_band", color_discrete_map=RISK_COLORS,
                     hover_data=["student_id"], title="Conscientiousness vs Success Score")
    st.plotly_chart(fig, use_container_width=True)
    fig = px.histogram(f, x="stress_level", nbins=25, title="Stress level distribution")
    fig.add_vline(x=75, line_dash="dot")
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------- Insights
with tab_ins:
    st.subheader("Key findings (computed automatically from the full dataset)")
    for line in generate_insights(df):
        st.markdown(f"- {line}")
    st.caption("Add your own insights in src/insights.py.")

# ----------------------------------------------------------------- Data quality
with tab_data:
    st.subheader("Data cleaning log")
    st.write("Every fix applied while merging the seven sources into one student view:")
    st.dataframe(log, use_container_width=True, hide_index=True)
    st.subheader("Success Score recipe")
    st.table(pd.DataFrame({"Indicator": INDICATORS, "Weight": [f"{w * 100:.0f}%" for w in C.WEIGHTS.values()]}))
    st.caption(f"High risk below {C.HIGH_RISK_BELOW}; Medium below {C.MEDIUM_RISK_BELOW}; otherwise Low.")

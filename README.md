
# Lunala: Student Success Platform

> **Every student seen, every step celebrated.**
> An early-support copilot for colleges. Lunala combines academics, attendance, LMS activity, wellbeing check-ins and behaviour trends into an explainable Student Success Score and early alerts, so faculty and counsellors can reach out kindly and early.



## Demo logins
| Role | Username | Password | What they see |
|---|---|---|---|
| Faculty | `faculty` | `faculty123` | Dashboard, at-risk list, alerts (gentle summaries only), Lunala |
| Counsellor | `counsellor` | `care123` | Full alert detail, psychometrics, survey quality, Lunala |
| Admin | `admin` | `admin123` | Everything, plus loading your own CSV data |
| Student | `S1010` | `1234` | The Lunala wellbeing check-in only |

*Demo sign-in runs in the browser. A real deployment needs server-side authentication.*

## Student experience (mobile-first)
Students get an **Opportunities** feed (hackathons, workshops, placement drives and clubs from universities and campus, with filters, personal picks, save, and add-to-calendar) a **Suggestion and complaint box** (anonymous option, reference codes to track replies, safety items routed to the counsellor), a **Faculty availability** box (who is free now, or at any chosen day and time, filterable by department; loaded from a faculty CSV) and a **My progress** home with their own attendance, LMS activity, grades, skills and weekly updates, plus an optional check-in. Events come from an events CSV that admins load (sample events are synthetic). They never see risk zones, alerts or the Success Score. Progress is the reason to open the app; the check-in is optional.

## The problem
Colleges hold data in disconnected systems (attendance, marks, LMS, placements, feedback) and use it only after a student has already failed or dropped out. Struggling students often show warning signs weeks earlier, but nobody sees them together.

## The solution
1. **Unified student view:** eight data sources are cleaned and merged on `student_id`, with every fix logged.
2. **Student Success Score (0-100):** seven weighted indicators (academic, attendance, LMS, engagement, placement readiness, feedback, psychometrics). Fully explainable: each student's points earned and lost per indicator.
3. **Risk flags and segments:** academic, placement and wellbeing flags with plain-English reasons, plus KMeans student segments with suggested actions.
4. **Lunala, the AI agent:**
   - *For students:* a navigator chat that guides them around the platform and can request a counsellor, plus a short, voluntary, conversational wellbeing check-in.
   - *For staff:* answers questions about the cohort, briefs you each day, explains any alert, and drafts a caring check-in message.
5. **Psychometric engine:** short validated-style scales (WHO-5, PSS-4, UCLA-3, PHQ-2, GAD-2, belonging, study confidence) with reverse scoring, Cronbach's alpha, cohort norms, response-quality checks (straight-lining, speed, inconsistency) and the Reliable Change Index to separate real change from noise.
6. **Early alerts with a human in the loop:** survey signals plus behaviour trends (attendance and LMS decline) become Urgent / High / Watch alerts. An alert needs two independent sources to reach High. Counsellor capacity planning and a follow-up tracker close the loop.

## How it maps to the judging criteria
| Criterion | Where to look |
|---|---|
| Data integration and analysis (30%) | Data cleaning log tab; `python-pipeline/src/pipeline.py` |
| Success Score and risk identification (25%) | `docs/score_note.md`; Early alerts; Segments (bonus) |
| Dashboard and visualization (25%) | Overview, Student detail (explainable score, bonus), Psychometrics |
| Problem understanding (10%) | Role-based views for faculty, counsellors, students and admins |
| Presentation and demo (10%) | Lunala briefing and chat; sign in as each role |

## Responsible by design
- Voluntary check-ins with transparent consent, and a self-referral option.
- Faculty see only gentle summaries. Survey answers are visible to counsellors only.
- Screens are **not diagnoses**. Every alert goes to a human.
- No hobby or personality stereotyping: alerts rely on a student's own behaviour change and self-reported wellbeing.
- Data stays in the browser. No data is sent anywhere.
- See `docs/ethics-and-privacy.md`.

## Tech
Single-file web app (HTML, CSS, JavaScript, Chart.js) so it deploys on GitHub Pages with no server. Python pipeline (pandas, scikit-learn, Streamlit) in `python-pipeline/` for the data-science workflow.

## Run it
- **Web app:** open `index.html` in a browser (needs internet for fonts and charts), or use the GitHub Pages link.
- **Python pipeline:** see `python-pipeline/README.md`.

## Honest limitations
- All data is **synthetic**; patterns are partly planted by the generator.
- Scales are short adapted forms. Real use needs licensed originals and local validation, including fairness checks.
- Norms are local to the cohort, not national.
- The web app's AI mode (open-ended questions) works inside Claude; elsewhere Lunala runs in offline mode using built-in tools.
- Weights and thresholds are judgement calls to be tuned on real data.

## Roadmap
Server-side authentication and audit logs, a database, a Python port of the survey engine, fairness dashboards across departments and genders, and a belonging matcher that suggests clubs from optional interests (never used to score risk).

## Team
**Team name:** <TEAM IMPERIAL Z>

| Member | Role |
|---|---|
| Srivasthaw | Designed and built the full solution: architecture, backend, frontend, wellbeing survey, early-alert scoring, Lunala agent |
| Shaktivel (Team lead) | Tested the app and reported bugs |
| Shree Hari | Suggested improvements |
| Dhanyasree | Reviewed privacy and misuse risks |
| Athulyaa | Reviewed documentation |

College: Marwadi_University, Rajkot

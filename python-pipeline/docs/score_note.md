# Student Success Score: methodology note

**Purpose.** One 0-100 number per student that combines academic and engagement signals, so faculty can spot who needs help early.

## Step 1: Six indicator scores (each 0-100)
| Indicator | Built from | Formula |
|---|---|---|
| Academic | CGPA, backlogs | 0.7 x (CGPA x 10) + 0.3 x (100 - 25 x backlogs, min 0) |
| Attendance | Overall attendance % | used as is |
| LMS | Logins per week, assignment completion | 0.4 x min(logins/10, 1) x 100 + 0.6 x completion % |
| Engagement | Events, clubs, hackathons, certifications | 8 x events + 10 x clubs + 15 x hackathons + 12 x certifications (max 100) |
| Placement | Aptitude, coding, mock interview, skills | 0.7 x average of 3 tests + 0.3 x skills (0.6 x technical level + 0.4 x soft skill) |
| Feedback | Student satisfaction, faculty feedback (1-5) | average / 5 x 100 |
| Psychometrics | Conscientiousness, emotional stability, grit, motivation, stress level (all 0-100) | (sum of the four positive traits + (100 - stress)) / 5 |

## Step 2: Weighted sum
Academic 30% + Attendance 20% + LMS 10% + Engagement 10% + Placement 15% + Feedback 5% + Psychometrics 10%.
Weights are defined in `src/config.py` and are a team judgement, not an industry standard. Academic carries the most weight because it is the most direct measure of performance.

## Step 3: Risk identification
- **Risk band:** High below 50, Medium below 70, Low otherwise.
- **Academic risk flag:** CGPA below 6, or attendance below 60%, or 3+ backlogs.
- **Placement risk flag:** test average below 45, or coding below 35, or mock interview below 35.
- **Wellbeing (psychometric) flag:** stress above 75, emotional stability below 35, or grit below 35.
Every triggered rule is shown as a plain-English reason.

## Psychometrics: how to use them responsibly
- Traits come from self-report questionnaires (Big Five plus grit, motivation and stress). Openness, extraversion and agreeableness are shown in the dashboard but not scored, because they do not clearly predict success.
- Psychometrics are **not** a medical or clinical diagnosis. A wellbeing flag means "offer support", not "something is wrong with this student".
- Real data needs informed consent, secure storage and limited access. Do not use these scores to rank students or make admission, placement or disciplinary decisions.
- Our data is synthetic, so the trait patterns (for example stress rising with backlogs) were planted by the generator.

## Step 4: Explainability
Each student's score is split into points earned and points lost per indicator, and the indicator with the most lost points is labelled the **biggest drag**.

## Step 5: Segmentation (bonus)
KMeans (k=4) groups students on the six indicator scores. Clusters are named by rules on their averages and each has a suggested action.

## Known limitations (be honest about these in your demo)
- Data is synthetic, so patterns are partly planted by the generator.
- Weights and thresholds are judgement calls and should be validated against real outcomes.
- Missing values are filled with the median, which can hide real gaps.

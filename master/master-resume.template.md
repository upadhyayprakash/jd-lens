# Master resume data: YOUR NAME

> **EXAMPLE TEMPLATE.** Everything below is made-up sample data so the extension has something to read on day one.
> Replace it with your own details, keep the headings and table layouts exactly as they are, then run
> `python3 tools/build_profile.py`. Delete this note when you are done. The parser needs: the `Career start` row, the
> `## 1.` to `## 6.` headings, `### Company, Title (period, location)` headings, fact lines like `- **F-AB-01** (verified) text`,
> and the skills tables. Do not add anything you cannot back up: every skill in section 5 must say how you know it.

Single source of facts for scoring job descriptions, tailoring resumes and answering application questions.

**How levels work (section 5).** `listed` = it is on your resume. `user-confirmed` = you told Claude or wrote it here. `partial` = real but limited (a certificate, or learning only; counts half). `earlier` = only on an older resume (does not count until you confirm it). `none` = no evidence.

---

## 1. Identity and constraints

| Field | Value |
|-------|-------|
| Name | YOUR NAME |
| Headline | Senior Software Engineer (example) |
| Career start | Jul 2014 (Example Corp). |
| Education | B.Tech Computer Science, Example University, 2010 to 2014 |

**Job-search constraints**
- Region or work mode you need (for example: remote, India-based hiring).

---

## 2. Summary variants (for the top of a resume)

- **S-MAIN (current resume):** Software engineer with 10+ years building web products with TypeScript, React and Node.js. Led the checkout rebuild at Example Corp (latency cut 60%). [F-EX-01]
- **S-ALT (backend focus):** Backend engineer with 10+ years in Node.js, PostgreSQL and event-driven systems on AWS. [F-EX-02]

---

## 3. Experience facts

### Example Corp, Senior Software Engineer (Jan 2021 to now, Remote)

- **F-EX-01** (verified) Led the checkout rebuild in React and TypeScript, cutting latency by 60% across web and mobile web.
- **F-EX-02** (verified) Built the order-events pipeline on Kafka and Node.js, processing 2M events a day.
- **F-EX-03** (verified) Designed the PostgreSQL schema for the billing service, with role-based views for dashboards.

### Sample Startup, Software Engineer (Jul 2014 to Dec 2020, Bengaluru)

- **F-SS-01** (verified) Built the admin dashboard (React, Express, MySQL) used by 200 internal staff.

---

## 4. Awards, patent, certifications, open work

- **F-CE-01** (verified) AWS Certified Developer, Associate.
- **F-AW-01** (verified) Winner, Example Corp hackathon, 2022.

---

## 5. Skills inventory

Evidence = fact IDs from sections 3 and 4. `years` is optional. Levels are explained at the top.

### Frontend
| Skill | Level | Evidence | Years | Notes |
|-------|-------|----------|-------|-------|
| React (function components, hooks) | listed | F-EX-01, F-SS-01 | | |
| TypeScript | listed | F-EX-01 | | |
| Jest | listed | F-EX-01 | | |

### Backend
| Skill | Level | Evidence | Years | Notes |
|-------|-------|----------|-------|-------|
| Node.js | listed | F-EX-02 | | |
| Express.js | user-confirmed | F-SS-01 | since 2014 | |
| Kafka | listed | F-EX-02 | | |
| REST APIs | listed | F-EX-02 | | |

### Data
| Skill | Level | Evidence | Years | Notes |
|-------|-------|----------|-------|-------|
| PostgreSQL | listed | F-EX-03 | | |
| MySQL | listed | F-SS-01 | | |

### Infra and delivery
| Skill | Level | Evidence | Years | Notes |
|-------|-------|----------|-------|-------|
| AWS | listed | F-CE-01 | | |
| Docker | listed | F-EX-02 | | |
| Kubernetes | partial | F-CE-01 | | Course only. |

---

## 6. Role-type positioning (which facts lead)

| If the JD is mostly... | Lead with |
|------------------------|-----------|
| Product full-stack | F-EX-01, F-SS-01 |
| Backend or platform | F-EX-02, F-EX-03 |

---

## 7. Things a recruiter or ATS may flag

- Gaps in employment, title changes between versions, numbers with no source. Note how you would explain each.

---

## 8. Open confirmations

- [ ] Skills you think you have but have not confirmed yet (add them to section 5 as `user-confirmed` when you do).

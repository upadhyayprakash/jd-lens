# Master resume data: Anika Verma (sample)

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
| Name | Anika Verma |
| Location | Remote (US time zones) |
| Email | anika.verma@example.com |
| Phone | +1 (555) 010-0142 |
| Portfolio | anikaverma.example.com |
| LinkedIn | /in/example-anika-verma |
| GitHub | github.com/example-anika-verma |
| Headline | Senior Software Engineer · TypeScript, React, Node.js |
| Career start | Jul 2014 (Brightwave Systems). |
| Education | B.E. Computer Science, Hillcrest Institute of Technology, 2010 to 2014 |

The contact rows above fill the contact block of a tailored resume. Replace all of them with your own.

**Job-search constraints**
- Region or work mode you need (for example: remote, India-based hiring).

---

## 2. Summary variants (for the top of a resume)

- **S-MAIN (current resume):** Software engineer with 10+ years building payments and checkout products with TypeScript, React and Node.js. Cut checkout latency by 62% at Northwind Labs and built the feature-flag service that now runs on 40 product teams. [F-NW-01, F-NW-02]
- **S-ALT (backend focus):** Backend engineer with 10+ years in Node.js, NestJS, PostgreSQL and event-driven systems on AWS, from a 2M-events-a-day pipeline to a microservices billing platform. [F-BW-01, F-NW-03, F-NW-04]

---

## 3. Experience facts

### Northwind Labs, Senior Software Engineer (Jan 2021 to now, Remote)

- **F-NW-01** (verified) Led the checkout rebuild in React and TypeScript, cutting p95 latency from 420 ms to 160 ms (62%) across web and mobile web.
- **F-NW-02** (verified) Built Relay, an internal feature-flag service on NestJS and Redis, now used by 40 product teams with zero-downtime rollouts.
- **F-NW-03** (verified) Designed the PostgreSQL schema for the billing service, with role-based views for finance dashboards.
- **F-NW-04** (verified) Split the billing and notification modules out of the monolith into microservices that talk over Kafka events.
- **F-NW-05** (verified) Introduced Storybook for the shared component library and Mocha and Chai contract tests for the services.

### Brightwave Systems, Software Engineer (Jul 2014 to Dec 2020, Pune)

- **F-BW-01** (verified) Built the order-events pipeline on Kafka and Node.js, processing 2M events a day.
- **F-BW-02** (verified) Built the admin dashboard (React, Express, MySQL) used by 200 support staff, cutting ticket handling time by 25%.
- **F-BW-03** (verified) Shipped the REST APIs behind the customer mobile app, with automated tests in Jest.

---

## 4. Awards, patent, certifications, open work

- **F-CE-01** (verified) AWS Certified Developer, Associate.
- **F-CE-02** (verified) Completed an online Kubernetes administration course (learning only, no production use).
- **F-AW-01** (verified) Winner, Northwind Labs hackathon, 2024, smart refunds prototype.
- **F-OW-01** (verified) Maintainer of a small open source TypeScript client for feature flags.

---

## 5. Skills inventory

Evidence = fact IDs from sections 3 and 4. `years` is optional. Levels are explained at the top.

### Frontend
| Skill | Level | Evidence | Years | Notes |
|-------|-------|----------|-------|-------|
| React (function components, hooks) | listed | F-NW-01, F-BW-02 | | |
| TypeScript | listed | F-NW-01, F-OW-01 | | |
| Jest | listed | F-BW-03 | | |
| Storybook | listed | F-NW-05 | | |

### Backend
| Skill | Level | Evidence | Years | Notes |
|-------|-------|----------|-------|-------|
| Node.js | listed | F-BW-01, F-NW-02 | | |
| Express.js | user-confirmed | F-BW-02 | since 2014 | |
| NestJS | listed | F-NW-02 | | |
| Kafka | listed | F-BW-01, F-NW-04 | | |
| REST APIs | listed | F-BW-03 | | |
| Microservices | listed | F-NW-04 | | |

### Testing
| Skill | Level | Evidence | Years | Notes |
|-------|-------|----------|-------|-------|
| Mocha | listed | F-NW-05 | | |
| Chai | listed | F-NW-05 | | |

### Data
| Skill | Level | Evidence | Years | Notes |
|-------|-------|----------|-------|-------|
| PostgreSQL | listed | F-NW-03 | | |
| MySQL | listed | F-BW-02 | | |
| Redis | listed | F-NW-02 | | |

### Infra and delivery
| Skill | Level | Evidence | Years | Notes |
|-------|-------|----------|-------|-------|
| AWS | listed | F-CE-01 | | |
| Docker | listed | F-BW-01 | | |
| Kubernetes | partial | F-CE-02 | | Course only. |
| Go | earlier | | | On an older resume only; confirm before use. |
| Prometheus | earlier | | | On an older resume only; confirm before use. |

---

## 6. Role-type positioning (which facts lead)

| If the JD is mostly... | Lead with |
|------------------------|-----------|
| Product full-stack | F-NW-01, F-BW-02 |
| Backend or platform | F-NW-02, F-NW-03, F-NW-04 |

---

## 7. Things a recruiter or ATS may flag

- Gaps in employment, title changes between versions, numbers with no source. Note how you would explain each.

---

## 8. Open confirmations

- [ ] Skills you think you have but have not confirmed yet (add them to section 5 as `user-confirmed` when you do).

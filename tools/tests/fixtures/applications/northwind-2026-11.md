---
company: Northwind
role: Senior Full Stack Engineer - EMEA
applied: 2026-11-21
source: https://www.northwind.example/careers/job/1946e291-2f42-4d70-9306-6582f6506b61/?source=linkedin
resume: tailored/northwind-2026-11/alex_morgan_resume_northwind.pdf
status: applied                    # considering | applied | screening | interviewing | offer | rejected | withdrawn
fit_score: 86                      # 70 * must-have score + 30 * nice-to-have score (see .claude/skills/job/SKILL.md)
posted: 2026-06-03
captured: 2026-11-21
keywords: TypeScript, JavaScript, React, Express, NestJS, Vite, Next.js, PostgreSQL, REST, microservices, asynchronous, Jest, Mocha, Chai, Storybook, React Testing Library, Cypress, Docker, Kubernetes, AWS, remote, SaaS
---

# Northwind: Senior Full Stack Engineer - EMEA

Team: Full-Stack Engineering. Full-time. Remote-first. Salary range: $60,000 - $100,000 USD gross base, localized to the candidate's country currency.
Locations listed: India, Pakistan, Philippines, Indonesia, Belgium, Czech Republic, Estonia, Croatia, Armenia, Egypt, Albania, Georgia, Greece, North Macedonia, Romania, Italy, Serbia, Kosovo, Slovenia, Portugal, Ukraine, Spain, Slovakia.

## Open checks before applying

- Posted 2026-06-03, about 5.5 months old. Check the posting is still live and accepting applications.
- Title says EMEA but India is on the location list. The page never says "India remote" in words. Confirm with recruiting that India-based hiring is real for this role.
- Salary band ($60k to $100k USD, localized) may land below the target. Check against expectations before investing time.
- The page says AEDT and AI systems assist evaluation of "experience level, technical skills and qualifications". Keyword coverage in the resume matters (see ATS check below).

## Fit snapshot (against the base resume, first pass)

Strong:
- 8+ years full-stack with TypeScript focus: 10+ years, TypeScript across Lumenly, own products.
- React (function components, hooks): TipTap v3 migration at Lumenly, PayPlus frontend revamp, EventHub live video tile engine.
- Node, NestJS, Next.js (both are "a plus" in the JD): on resume.
- Postgres, schema and query work: PostgreSQL on resume, OLAP queries materialised at Brightlabs (40% faster pages).
- Microservices, async, events: Kafka, BullMQ, Redis, event-driven design, NestJS job service with handler registry.
- 24/7 SaaS on a major cloud: Lumenly at about 9K req/s peak, AWS at Payly, Cloudflare.
- Docker and Kubernetes: on resume.
- Domain match: PayPlus payments (2.4M transactions/day, PIN and 2FA SDK) is the closest evidence for a payroll and payments platform. Lead with it.

Updated 2026-11-21 after the user confirmed Express, React Testing Library, Storybook, Mocha, Chai, Postgres and MySQL schema design, and Kafka (see `master/master-resume.md`: F-USR-01..05, F-BR-04). These skills are real but were left off the Oct resume to keep it to 2 pages.

Still not covered:
- Cypress and Vite: not confirmed, so not claimed. Playwright covers end-to-end testing; say so honestly if asked.
- Kubernetes: certificate and "learning" only. Docker is solid. It is a "brownie points" item, not a must-have.
- Resume headline is "Senior Full-Stack Engineer · AI Product Engineering", while this role is core product engineering. Use the S-FS summary (master section 2).

## Score (provisional, my own judgment, not an official ATS score)

| Measure | Result |
|---------|--------|
| Must-haves met by master data | 11 of 11 (TypeScript, React, Express, Postgres, 8+ years, remote-first, communication, ownership, testing, customer focus, code quality). Code reviews and "stakeholder communication" rest on lead-role facts (F-PY-03), not a dedicated example. |
| Nice-to-haves met | 4 of 4 groups, partly: 24/7 cloud SaaS yes, REST and microservices and async yes, testing frameworks yes except Cypress, Docker yes and Kubernetes weak. |
| JD keywords visible on the base resume as written | 11 of 22 (about 50%). Missing: JavaScript, Express, Vite, microservices, asynchronous, Mocha, Chai, Storybook, React Testing Library, Cypress, SaaS. |
| JD keywords after the proposed edits below | 20 of 22 (about 91%). Still missing: Vite and Cypress (not claimed). |

The Oct resume undersells you for this JD. The experience is there; the keywords are not on the page.

## Tailored resume (built 2026-11-21, all five changes approved)

- PDF: `tailored/northwind-2026-11/alex_morgan_resume_northwind.pdf` (2 pages, A4, text extracts cleanly)
- Source: `tailored/northwind-2026-11/alex_morgan_resume_northwind.html` (same layout as the base artifact; printed with headless Chrome)
- Measured on the finished PDF: 20 of 22 JD keywords present. Missing: Vite, Cypress (not claimed).
- Summary wording differs slightly from the master draft: "Led teams on" became "Led" (no team-lead fact on file) and "SaaS" was added.
- Left out vs the Oct resume: Turso/R2/PyTorch/TensorFlow skills tags, the Context-manifests bullet and the twelve-agents bullet (folded into one line).
- The "Own products" entry from the Oct resume was restored on request (2026-11-21), with the same public wording as before.

## Tailoring proposal (original, approved)

Goal: one tailored 2-page resume, same layout as the base resume. Page 2 has spare room at the bottom.

1. **Headline:** "Senior Full-Stack Engineer · TypeScript, React, Node.js".
2. **Summary:** use S-FS from master section 2 (the user's edited wording). Add the words "SaaS" and "microservices" only if they fit naturally.
3. **Skills block** (keywords the JD names, all confirmed):
   - Frontend: React, Next.js, TypeScript, JavaScript, TipTap, Tailwind CSS, Jest, React Testing Library, Storybook, Playwright
   - Backend: Node.js, Express, NestJS, REST APIs, Microservices, Kafka, Redis, BullMQ, Event-driven design
   - Testing: Jest, Mocha, Chai, React Testing Library, Storybook, Playwright
   - Data: PostgreSQL, MySQL, MongoDB
   - Infra: AWS, Docker, Kubernetes, CI/CD (GitLab CI, GitHub Actions), Nx
   - To free space: shorten or drop Turso, R2, PyTorch/TensorFlow and the Claude-specific skills line for this version.
4. **Brightlabs bullet** (F-BR-02, F-BR-04): "Built admin dashboards with RBAC for health, retail, aerospace and co-working clients. Designed production Postgres and MySQL schemas, denormalised tables and role-based views for real-time dashboards; materialised OLAP queries and client caching cut page load by 40%."
5. **Lumenly bullet 3** (F-LM-04): use the words "asynchronous" and "microservices" if they are accurate: "extended the NestJS asynchronous job service...". the user to confirm the wording.
6. **Own products:** shorten the Agentic PR Platform and Starter Kit bullets to make room. For a product-engineering reader, keep one line each. Do not remove them: they show ownership and range.
7. **Do not add:** Cypress, Vite, any Express or Kafka project claim (no project or number on file; see master open confirmations). Do not write "in TypeScript" inside a Lumenly bullet until TypeScript use there is confirmed.

Final step before applying: re-count keywords on the finished PDF, check it is 2 pages, and confirm the text extracts cleanly (ATS readability).

## JD (role-relevant parts, verbatim)

**Summary**

The Senior Full Stack Engineer is responsible for designing, developing, and maintaining both the front-end and back-end components of Northwind's platform. You will work on a wide range of technologies and systems, from the user-facing interface to the server-side infrastructure, ensuring seamless integration across Northwind's global platform. You will be part of a cross-functional team that collaborates closely with Product, Design, and DevOps teams to deliver high-quality, scalable, and secure solutions that power Northwind's global workforce and payroll services.

**Responsibilities**

- You will develop high-quality, responsive web applications using TypeScript, Javascript, React, Express. Experience with NestJS, Vite, and Next.js is a plus.
- You will design and implement server-side APIs, data models, and business logic using mainly Express framework
- You will create client-side function-based React components, hooks, stories, and tests to interact with your server-side work
- You will create and optimize database schemas, queries, and interactions with Postgres.
- You will build reusable and modular components on both the front and back end that promote code reusability, maintainability, and scalability.
- You will perform thorough testing, debugging, and troubleshooting of applications to ensure high-quality deliverables.
- You will stay updated with emerging web development trends, frameworks, and best practices, and recommend improvements to enhance development processes.
- You will participate in code reviews and provide constructive feedback to team members to maintain code quality standards.
- You will communicate project progress, challenges, and solutions effectively to team members and stakeholders.
- Contribute to the continuous improvement of development processes, methodologies, and tools.

**Qualifications**

- At least 8 years of Full-Stack experience, with a focus on TypeScript development.
- Expert in the art of designing, coding, testing, and maintaining applications using the tech listed above.
- Thrive in a collaborative, remote-first work culture where teamwork and camaraderie are key.
- Embrace independence and take ownership of your projects, yet also excel in a team setting and love to contribute.
- Communicate complex ideas with ease and enjoy collaborating with diverse teams of technical and non-technical stakeholders.
- Are passionate about solving customer problems with your coding superpowers, and are a natural at troubleshooting issues.
- Take a business-focused approach to software development, with a keen eye on delivering high-value outcomes for our clients.
- Obsess over details, and always keep the customer experience top of mind.

**Extra brownie points if you:**

- Have experience with SaaS products running 24/7 on a major cloud vendor.
- Solid understanding of RESTful APIs, microservices architecture, and asynchronous programming.
- Experience with testing frameworks (Jest, Mocha, Chai, Storybook, React Testing Library) and automated testing methodologies (Cypress).
- Knowledge of containerization technologies (Docker, Kubernetes)

**Total rewards (relevant)**

- Salary ranges are quoted in USD as a consistent global reference. Offer is localized to the country's currency using a market-aligned conversion.
- Stock grant opportunities dependent on role, employment status and location.
- Optional flexible working office membership, with IWG.

**Process notes**

- Northwind communicates with applicants from @northwind.example (and @payspace.com, @paygroup.com). Be wary of other senders.
- Accommodation requests: recruiting@northwind.example.
- Process may use Automated Employment Decision Tools and AI to assist evaluation, with human oversight of final decisions.

## Questions

None yet.

## Rounds

| Date | Round | Interviewer | Notes | Result |
|------|-------|-------------|-------|--------|

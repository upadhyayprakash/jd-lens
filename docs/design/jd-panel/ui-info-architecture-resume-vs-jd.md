The key architectural decision is to distinguish **global navigation, job-specific analysis, and application management**. These should not become six independent screens competing for space in the Chrome sidebar.

I'd structure the extension around three functional areas:

1. **JD Fit** – Understand how well the current job matches your master resume.
2. **Resume** – Manage the master profile and the evidence used for scoring.
3. **Applications** – Track jobs you've saved, applied to, and progressed through.

Below is a component and navigation specification you can hand directly to Claude.

# JD Fit — UI Information Architecture

## 1. Product structure

The extension has three primary functional areas:

- **JD Fit:** Job description analysis and resume matching.
- **Resume:** Master resume data, skills, experience and profile management.
- **Applications:** Saved jobs, application history and recruitment pipeline.

The Chrome extension sidebar is the primary interface. Settings and the full application management experience can use dedicated pages when more space is needed.

## 2. Global application shell

Every sidebar view should share the same application shell.

**Header**

- Brand icon and product name: JD Fit
- Pin/unpin extension action
- Close extension action
- Optional compact settings shortcut

**Primary navigation**

- JD
- Resume

Use a compact segmented navigation control directly below the header.

The currently selected section should have a subtle peach-to-orange gradient treatment.

**Contextual navigation**

- JD section: Overview, Analysis, Details
- Resume section: Profile, Skills, Experience

Avoid adding every subsection to the global navigation. Use contextual tabs or collapsible sections inside each primary area.

## 3. JD section

This is the default landing screen when a user opens a supported job posting.

### A. Job Overview (default view)

Purpose: Give the user an immediate assessment of the current job.

Components:

- Job saved/applied indicator, with a link to application details.
- Job summary card:
  - Job title
  - Company
  - Location
  - Job posting URL
  - Posting date
- Match score card:
  - Score out of 100
  - Score change compared with previous evaluation, if available.
- Salary offered:
  - Salary range when available
  - Not stated when unavailable
  - Ability to update manually
- Threshold control:
  - User-defined minimum acceptable score.
- Flags:
  - Missing or ambiguous requirements
  - Remote/hybrid/location considerations
  - Experience mismatches
  - Other relevant observations.
- Evidence summary:
  - Matched requirements
  - Missing requirements
  - Unconfirmed requirements
- CTA: View full analysis.

### B. Analysis

Purpose: Explain WHY the job received its match score.

Components:

- Overall match score and visual indicator.
- Matched skills.
- Missing skills.
- Additional skills.
- Skill overlap tags.
- Evidence-based comparison between JD requirements and master resume.
- Experience and seniority alignment.
- Potential concerns or ambiguities.
- Recommended next steps.

Next steps should be actionable:

1. Tailor resume to the job.
2. Review missing skills and add supporting evidence if applicable.
3. Review the final match before applying.

Where appropriate, provide actions such as:

- Use Claude to propose resume edits.
- View skill gaps.
- Mark an action as completed.

Include a compact Pro Tip or contextual recommendation card.

### C. Details

Purpose: Preserve the original job posting information and provide traceability.

Components:

- Job title, company, location and posting date.
- Job highlights.
- Required skills and qualifications.
- Job description, with expandable content.
- Your match percentage.
- Skills overlap.
- Link to the original job posting.

Do not duplicate the entire analysis here. Details should represent the source job information; Analysis should represent the evaluation.

## 4. Resume section

Purpose: Maintain a single source of truth for the user's professional profile.

### A. Master Resume

Components:

- Last updated timestamp.
- Open master resume as HTML.
- Open master resume as PDF.
- Short profile summary.
- Skills and technologies.
- Professional experience.
- Projects.
- Education.
- Certifications.
- Affiliations.

### B. Skills and Experience

Organize the profile into independently manageable sections:

- Technical skills
- Frameworks and tools
- Engineering competencies
- Domain experience
- Professional experience
- Projects and achievements
- Education and certifications

Skills should support evidence references wherever possible.

For example, a skill should be linked to the experience or project that demonstrates it.

### C. Profile management

Actions:

- Edit profile information.
- Add or remove skills.
- Update experience and achievements.
- Rebuild skill profile.
- Recalculate job matches when master data changes.

Important: The master resume is the source of truth. A job-specific resume variation should not silently overwrite it.

## 5. Applications section

Purpose: Track every job opportunity from discovery through the final hiring outcome.

This section should preferably open as a dedicated full-page extension view rather than squeezing a complete application dashboard into the narrow sidebar.

### A. Application Dashboard

Components:

- Total saved jobs.
- Applied jobs.
- Interviewing.
- Offers.
- Rejections.
- Withdrawn applications.

Provide filtering by application status:

- All
- Applied
- Interviewing
- Considering

Each application card should show:

- Company
- Job title
- Match score
- Application status
- Date added
- Date applied, when available

Default sorting: Most recent activity or highest match score.

### B. Application Details

Opening an application should display:

**Job information**

- Company and role.
- Location.
- Posting date.
- Match score.
- Current application status.

**Files**

- Resume submitted (PDF).
- Original job posting.
- Full job details (HTML).
- Copy file path.

**Gaps noted**

- Notes about missing qualifications or concerns recorded when applying.

**Interview rounds**

- Round history.
- Round date.
- Interview type.
- Notes and outcome.
- Add new round action.

**Update status**

- Considering
- Applied
- Screening
- Interviewing
- Offer
- Rejected
- Withdrawn

Status changes should preserve application history rather than overwrite previous events.

## 6. Settings

Settings should be accessible from the header or application menu.

Organize settings into compact independent sections:

**Scoring**

- Minimum match threshold.
- Scoring preferences.

**Appearance**

- Theme: System / Light / Dark.
- Text size.

**Reading page**

- Automatic job-page reading.
- Supported job-page behavior.

**Local helper**

- Local repository connection status.
- Resume file location.
- Skill profile file location.
- Version information.

**Skill profile**

- Last generated timestamp.
- Number of skills and evidence entries.
- Show skill profile.
- Rebuild skill profile.

## 7. Navigation and component hierarchy

Recommended hierarchy:

Extension Shell\
├── Header\
├── Primary Navigation\
│   ├── JD\
│   │   ├── Overview\
│   │   │   ├── Job Summary\
│   │   │   ├── Match Score\
│   │   │   ├── Salary\
│   │   │   ├── Threshold\
│   │   │   ├── Flags\
│   │   │   └── Evidence Summary\
│   │   ├── Analysis\
│   │   │   ├── Score Breakdown\
│   │   │   ├── Matched Skills\
│   │   │   ├── Missing Skills\
│   │   │   ├── Extra Skills\
│   │   │   ├── Experience Alignment\
│   │   │   └── Next Steps\
│   │   └── Details\
│   │       ├── Job Highlights\
│   │       ├── Job Description\
│   │       └── Skills Overlap\
│   │\
│   └── Resume\
│       ├── Master Resume\
│       ├── Skills\
│       ├── Experience\
│       ├── Projects\
│       └── Education\
│\
├── Application Management (dedicated full-page view)\
│   ├── Application Dashboard\
│   └── Application Details\
│       ├── Job Information\
│       ├── Submitted Files\
│       ├── Gaps Noted\
│       ├── Interview Rounds\
│       └── Status History\
│\
└── Settings\
├── Scoring\
├── Appearance\
├── Reading Page\
├── Local Helper\
└── Skill Profile

## 8. UX and implementation guidelines

- Optimize the sidebar for a narrow viewport (approximately 350–400px).
- Keep global navigation persistent.
- Use tabs for closely related views, not for unrelated workflows.
- Prefer expandable sections for secondary information.
- Keep the match score visible and prominent.
- Avoid repeating the same information across Overview, Analysis and Details.
- Use consistent reusable components for score cards, skill chips, status pills, evidence lists and action buttons.
- Use skeletons or loading indicators while analyzing a new job.
- Support empty, loading, error and disconnected states.
- Maintain navigation state when switching between JD and Resume.
- Keep the current job context available when navigating between sections.
- Make every interactive element functional; avoid decorative buttons.

## 9. Visual design system

Use the existing dark/light design direction, with the following brand gradient:

Linear gradient:

- Start: #f5a8a0
- End: #f4c686

Use the gradient selectively:

- Active navigation indicator.
- Match score progress.
- Important CTA accents.
- Subtle card borders.
- Small background highlights.

Avoid applying gradients to large surfaces or every card.

Keep typography compact, with clear information hierarchy and sufficient contrast.

The UI should feel like a focused developer productivity tool, not a generic analytics dashboard.

## **3. Recommended navigation behavior**

This is how I'd expect the actual extension to behave:

**JD Fit — Chrome sidebar**

Persistent shell

**JD**

Current job analysis

**Resume**

Master profile

**JD contextual tabs**

Overview

Analysis

Details

Overview content

Job summary

Match score

Salary

Threshold

Flags and evidence

**Application management**

Full-page view

**Application dashboard**

All

Applied

Interviewing

Considering

**Company — Job title**

Applied

Match score · Date · Application details

## **4. One important architectural recommendation**

Don't make `Overview`, `Analysis`, and `Details` separate routes with independent data fetching and duplicated state.

Use a shared `JobContext` containing:

- Current job posting
- Parsed JD requirements
- Match evaluation
- Matched/missing skills
- Evidence references
- Application record

Then all three views consume the same context.

Similarly, `ResumeContext` should own the master profile and its evidence.

This will make it easier for Claude to build reusable components and prevent inconsistencies when the user updates their master resume or changes an application's status.

**My recommendation:** Keep the Chrome sidebar focused on evaluating the current job and accessing the master resume. Treat application tracking as a related but separate workflow, with a dedicated full-page experience.
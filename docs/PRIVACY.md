# Student Data Privacy Design

StoryTailor was built to be used by elementary students during class, so it is
designed around the rules that apply to a K-8 classroom tool in California.
This document maps each obligation to the control in the code that supports it.

> This is an engineering design note, not legal advice. A district deploying
> any classroom tool should review it under its own data privacy agreement.

## Principles

1. **Collect the minimum.** No names, birthdates, emails, photos, or voice. A
   student is a random pseudonym (`stu_3f9a...`) plus grade, reading level,
   and up to five interests. The teacher keeps the pseudonym-to-name roster
   on paper or in the school's own systems.
2. **The school stays in control.** Teachers create, export, pause, and delete
   student accounts. There is no self-signup and no parent or student email.
3. **Educational use only.** No ads, no analytics SDKs, no third-party
   trackers, no profiling beyond the reading level used to fit the next story.
4. **Nothing identifying leaves the server.** Free-text input is redacted
   before storage and before it reaches a model provider. Prompts carry no
   student identifier.
5. **Delete on a schedule and on request.** Retention is enforced by a job,
   and deletion is a hard delete.

## Requirement to control mapping

| Requirement | What it asks | Control in StoryTailor | Code |
|---|---|---|---|
| **FERPA** (20 U.S.C. 1232g; 34 CFR Part 99), school official exception | Vendor is under the school's direct control; records used only for the authorized purpose; parents can inspect records | Teacher-owned accounts; per-teacher access checks; full JSON export of everything stored about a student | `auth.teacher_owns_student`, `GET /api/students/<id>/export` |
| **COPPA** (16 CFR Part 312), school-authorized collection for under-13s | Collect only what the educational purpose needs; no commercial use; deletion on request | No direct identifiers collected; consent status per student (`school_authorized`, `pending`, `withdrawn`); withdrawn accounts are blocked immediately and purged | `schema.sql`, `POST /api/students/<id>/consent`, `privacy.purge_expired` |
| **SOPIPA** (Cal. Bus. & Prof. Code 22584) | No targeted advertising, no building non-educational profiles, no selling student data, reasonable security | No ads or trackers; profile is limited to reading level and interests; secrets stored only as keyed hashes; `Cache-Control: no-store` on every response | `privacy.hash_secret`, `create_app` response headers |
| **AB 1584** (Cal. Ed. Code 49073.1) | District owns the records; vendor deletes at end of contract; breach notification process | Records live in the district's own deployment (SQLite file it controls); retention job plus hard delete; audit log of every create, export, consent change, and deletion to support incident investigation and notification | `flask purge-expired`, `audit_log` table |
| **Model provider data use** | Student content should not train third-party models | OpenAI API requests use `store=False`; API data is not used for training by default; only redacted, pseudonymous prompts are sent; `offline` provider available for zero-egress classrooms | `llm.OpenAIProvider`, `STORYTAILOR_LLM_PROVIDER=offline` |

## Data inventory

| Data | Where | Why | Retention |
|---|---|---|---|
| Pseudonym, grade, target level, interests, avoid-topics | `students` | Fit stories to the reader | Until the teacher deletes the account or consent is withdrawn |
| Story topic (redacted), story text, sources, levels | `stories` | Let the student reread; let the teacher review | `STORYTAILOR_RETENTION_DAYS` (default 400) |
| Rating, difficulty vote, flag, comment (redacted) | `feedback` | Classroom feedback loop | Same as stories |
| Access-code hash, teacher-token hash | `students`, `teachers` | Sign-in | Lifetime of the account |
| Actor, action, pseudonym, timestamp | `audit_log` | Accountability for record access | Kept after deletion; holds no content |

## Redaction

`privacy.redact()` removes emails, URLs, phone numbers, street addresses,
long ID-like numbers, and self-introductions ("my name is ...") from anything
a child types. The kinds of PII removed (not the values) are written to the
audit log so a teacher can see when a student needs a reminder.

Regex redaction is a safety net, not a guarantee. The UI also tells students
not to type their name or address, and the topic field is capped at 120
characters.

## Operating checklist for a deployment

- Set a long random `STORYTAILOR_SECRET_KEY`. Rotating it invalidates every
  access code and teacher token by design.
- Run `flask purge-expired` daily (cron or a scheduled job).
- Serve over HTTPS only and restrict `ALLOWED_ORIGINS` to the school's front end.
- Sign the district's data privacy agreement (for example, the California
  Student Privacy Alliance template) before any student uses the system.

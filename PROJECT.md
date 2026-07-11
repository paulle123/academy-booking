# PROJECT.md — Context Brief & AI Handoff

> Paste this file at the top of any new AI chat. It contains everything needed
> to continue the project with zero prior context.

## What this is

A **white-label booking/enrollment system for a single tennis academy**,
built as a production-grade portfolio project by a CS student (confident
beginner: don't explain Python syntax; DO explain architecture, web patterns,
security and "why this way"). Real parents will create accounts, enter real
children's data and pay via Stripe **test mode** (live-ready via env var).
Interviews are in English — all code, docs and mentoring in English.

## Fixed stack — do not propose alternatives

- **Flask** (app-factory pattern, blueprints)
- **Raw sqlite3** — parameterized SQL only, NO ORM (learning goal: see the SQL)
- **Jinja2 + HTML/CSS** server-side rendering, no React, mobile-first
- **Stripe hosted Checkout** (never touch raw card data; PCI stays with Stripe)
- **Docker**, non-root user, gunicorn
- **Transactional email** via free-tier provider (Resend/Brevo), swappable via env vars

## Key decisions & stated assumptions

1. **Single academy instance, white-label**: name/branding/programs configurable
   via `settings` table + admin panel. True multi-tenancy = future stretch only.
2. **Prices in integer cents** (floats lose pennies; Stripe uses cents).
3. **Member vs non-member pricing** driven by `users.is_member`.
4. **`enrollments.amount_cents` is copied at enrollment time** — price changes
   never mutate agreed amounts.
5. **Enrollment is "paid" ONLY after a signature-verified Stripe webhook** —
   never trust the success redirect.
6. **Minimal PII for minors**: first name, birth year, optional UTR. Nothing else.
7. **Persistence caveat**: free hosts have ephemeral filesystems. Production DB
   must live on a persistent volume (Fly.io free volume) or Turso/libSQL.
   The data-access layer (`app/db.py`) is isolated so swapping SQLite→Postgres
   later only touches that file.
8. **Full schema created in Phase 1** (incl. tables used by later phases) so
   there are no migrations mid-project.
9. **Seed is idempotent** and runs on every container boot.
10. **Assumption**: Summer Camp priced $249/wk member, $299/wk non-member
    (spec said "model member/non-member" without figures; admin-editable later).
11. Demo accounts (parent@demo.test / Demo1234!, admin@demo.test / Admin1234!)
    are seeded and documented on purpose, so recruiters can evaluate in <1 min.

## Folder structure

```
academy-booking/
├── app/
│   ├── __init__.py        # create_app() factory, CSRF, error pages, /healthz, usd filter
│   ├── config.py          # ALL config from env vars
│   ├── db.py              # THE data-access layer: connection, init, idempotent seed, CLI
│   ├── schema.sql         # full schema, commented
│   ├── routes/
│   │   └── public.py      # blueprint "public": /, /programs
│   ├── templates/         # base.html, index.html, programs.html, errors/{404,500}.html
│   └── static/style.css   # mobile-first, no framework
├── run.py                 # local dev entry; prod = gunicorn in Dockerfile
├── Dockerfile             # non-root, layer-cached, init+seed+gunicorn on boot
├── requirements.txt / .gitignore / .env.example / README.md
└── PROJECT.md ROADMAP.md MENTOR_NOTES.md INTERVIEW_PREP.md CONTINUE_WITH_AI.md
```

Naming conventions: snake_case Python; tables plural; money columns end in
`_cents`; boolean-ish INTEGER 0/1 columns named `is_*`/`active`/`*_verified`;
blueprints named after their audience (public, auth, parent, admin).

## Database schema (text ERD)

```
settings(key PK, value)                          # white-label config
users(id PK, email UNIQUE NOCASE, password_hash, role CHECK parent|admin,
      is_member, email_verified, created_at)
children(id PK, parent_id FK->users ON DELETE CASCADE, name, birth_year, utr, created_at)
programs(id PK, name, description, min_age, max_age, utr_min, utr_max, active, sort_order)
program_options(id PK, program_id FK->programs CASCADE, label, days_per_week,
      billing_period CHECK session|week, price_member_cents, price_nonmember_cents,
      capacity NULL=unlimited, active)
enrollments(id PK, child_id FK->children CASCADE, option_id FK->program_options,
      status CHECK pending|paid|canceled, amount_cents, stripe_session_id,
      created_at, UNIQUE(child_id, option_id))
payments(id PK, enrollment_id FK CASCADE, stripe_payment_intent_id,
      amount_cents, currency, status, created_at)   # written ONLY by webhook
```

Relationships: users 1-N children; programs 1-N program_options;
children N-M program_options through enrollments; enrollments 1-N payments.

## Status

**DONE — Phase 1**: app factory, env config, full schema + WAL, idempotent seed
(6 programs, 15 options, demo parent+admin+child), public programs page with
member/non-member pricing, usd Jinja filter, CSRF initialized, 404/500 pages,
/healthz, mobile CSS, Dockerfile, README.
**REMAINS — Phases 2–7**: see ROADMAP.md (auth, children CRUD, enrollment flow,
admin panel, Stripe Checkout + webhook, hardening + tests, deploy).

## Non-negotiable production requirements (apply to every phase)

Parameterized SQL only · CSRF on all forms (Flask-WTF is initialized) ·
werkzeug password hashing · HttpOnly/SameSite/Secure cookies · secrets via env ·
rate-limit auth routes · server-side validation of ALL input · Stripe hosted
Checkout only, webhook signature verification, paid-only-via-webhook ·
WAL + persistent volume + backups · minimal minors' PII, privacy policy page,
no sensitive data in logs · friendly error pages, logging, /healthz,
mobile-responsive UI.

## Definition of done, per phase

A phase is done when: its routes work end-to-end locally AND in Docker; all new
forms have CSRF + server-side validation; all new SQL is parameterized; the
feature is usable on a phone; and the developer can explain every new concept
out loud (see MENTOR_NOTES.md). Phase-specific criteria in ROADMAP.md.

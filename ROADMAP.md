# ROADMAP.md — full project plan (Phases 2–7)

This is the intended design for the complete product. Current status:
Phases 2 and 3 are implemented as a working MVP (registration, login,
children management, enrollment). Email verification, password reset,
rate limiting, capacity checks, member/non-member pricing, enrollment cancellation, payments (Phase 5), and the admin panel (Phase 4) are planned but not yet built.

Each phase = goal → what it adds → key concepts learned → security notes → definition of done (DoD).

---

## Phase 2 — Parent accounts & children

**Goal:** self-service parent registration, login, and children management.

**Adds:** blueprint `auth` (`/register`, `/login`, `/logout`, `/verify/<token>`,
`/forgot-password`, `/reset/<token>`); blueprint `parent` (`/dashboard`,
`/children/add`, `/children/<id>/edit|delete`); templates for all of the above;
a `login_required` decorator; email sending module (`app/email.py`, provider
API via env vars); token generation with `itsdangerous` (signed, expiring).

**Concepts:** session-based auth (user_id in signed cookie), werkzeug
`generate/check_password_hash`, why plaintext/md5 are unacceptable, signed
expiring tokens for email verification & password reset, rate limiting
(Flask-Limiter: e.g. 5/min on login+register), IDOR prevention (every child
query filters `WHERE parent_id = ?` from session — never trust IDs from forms).

**Security:** never reveal whether an email exists ("if an account exists, we
sent a link"); hash comparison is constant-time via werkzeug; lock forms with
CSRF (already global); validate email format + password minimum server-side.

**DoD:** register → receive real verification email → verify → login → add 2
children → edit one → logout → login as other user cannot see them (test IDOR
manually). Rate limit returns 429 on the 6th rapid login attempt.

---

## Phase 3 — Enrollment

**Goal:** a parent enrolls a child into a program option.

**Adds:** `parent` routes: `/programs/<option_id>/enroll` (choose child, POST),
`/enrollments` ("my enrollments" with statuses), `/enrollments/<id>/cancel`;
Enroll buttons on the programs page (replace "coming soon"); price display by
membership status.

**Concepts:** the checkout funnel (enrollment created as `pending`, paid later);
capacity check (`COUNT(*) WHERE option_id=? AND status='paid'` vs capacity)
done in a transaction; UNIQUE constraint as the last line of defense against
double enrollment (catch IntegrityError and show a friendly message); copying
`amount_cents` at enrollment time.

**Security:** verify the child belongs to the logged-in parent AND the option
is active, server-side; age/UTR eligibility checks are soft warnings (parent
may override — business decision, document it).

**DoD:** enroll child → appears in "my enrollments" as pending with the correct
member/non-member price → cancel works → cannot enroll same child twice into
the same option → full flow works on a phone screen.

---

## Phase 4 — Admin panel

**Goal:** the academy owner runs the business from `/admin`.

**Adds:** blueprint `admin` with `admin_required` decorator (role check on top
of login); `/admin` dashboard (counts, revenue-so-far); `/admin/enrollments`
(all, filterable by program/status, cancel button); `/admin/students`;
`/admin/programs` CRUD + option CRUD (this is what makes the product
white-label); `/admin/settings` (academy name, tagline, contact).

**Concepts:** role-based access control in one decorator; soft-delete
(`active=0`) vs hard delete and why history must survive; server-side forms
for CRUD without JS frameworks.

**Security:** every admin route behind `admin_required`; admin actions logged
(who did what, when) — log line per mutation; no PII in logs (log IDs, not names).

**DoD:** demo admin can create a new program + options and it instantly appears
on the public page; can cancel any enrollment; a parent hitting /admin gets 403.

---

## Phase 5 — Stripe hosted Checkout

**Goal:** real (test-mode) payment completes the enrollment.

**Adds:** "Pay" button on pending enrollments → creates a Stripe Checkout
Session (server-side, amount from DB — never from the form) → redirect to
Stripe → `/pay/success` + `/pay/cancel` pages → `POST /webhooks/stripe`
(CSRF-EXEMPT — document why: Stripe can't send our token; security comes from
signature verification instead) verifies `Stripe-Signature` with
`STRIPE_WEBHOOK_SECRET`, marks enrollment `paid`, inserts a `payments` row,
sends confirmation email. Test-mode banner on checkout page with card
`4242 4242 4242 4242` (shown only when key starts with `sk_test_`).

**Concepts:** why hosted Checkout (PCI scope stays with Stripe); webhook
vs redirect as source of truth (user can close the tab after paying);
idempotent webhook handling (Stripe retries — handle duplicate events by
checking current status first); `stripe listen` CLI for local webhook testing.

**Security:** verify webhook signatures; never trust client-provided amounts;
success page reads status from DB (may still show "processing" until webhook
lands — handle that state).

**DoD:** full flow with test card ends with enrollment `paid`, a `payments`
row, and a confirmation email; a forged webhook (wrong signature) is rejected
with 400; replaying the same event doesn't double-mark.

---

## Phase 6 — Production hardening

**Goal:** safe to run for real families.

**Adds:** logging config (INFO to stdout — Docker-friendly; request id);
pytest suite (auth flow, IDOR attempt, enrollment constraints, webhook
signature rejection, health check); Privacy Policy + Terms pages (minors:
minimal data, parental consent is inherent — parent enters the data; deletion
on request); backup script (sqlite3 .backup to a dated file + restore doc);
security headers (CSP basic, X-Content-Type-Options, Referrer-Policy);
final mobile pass.

**DoD:** `pytest` green; error pages friendly; headers verified with curl;
backup/restore rehearsed once; privacy/terms linked in footer.

---

## Phase 7 — Launch

**Goal:** public HTTPS URL.

**Adds:** deploy to Fly.io (free volume mounted at /data → DATABASE_PATH) or
Render + Turso (swap sqlite3 connection for libsql client in db.py ONLY);
env vars set in host dashboard; Stripe webhook endpoint registered (test
mode); README gets screenshots + live URL + demo credentials + "switch to
live = change 3 env vars" section; final `.gitignore` audit (no .env, no .db
ever committed — check `git log` too).

**DoD:** fresh incognito browser: register → verify email → add child →
enroll → pay with test card → paid status + email received. Container
redeployed → data still there. README lets a stranger do all of the above
in under a minute with demo creds.

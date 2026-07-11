-- Academy Booking — full schema (all phases).
-- Phase 1 uses: settings, programs, program_options.
-- users/children/enrollments/payments are created now so the schema is stable
-- and later phases only add code, not migrations.

PRAGMA foreign_keys = ON;

-- White-label configuration: academy name, tagline, contact — editable by admin (Phase 4).
CREATE TABLE IF NOT EXISTS settings (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

-- Parents and admins. One table, role column — simpler than two tables,
-- and role checks happen in one decorator (Phase 4).
CREATE TABLE IF NOT EXISTS users (
  id             INTEGER PRIMARY KEY,
  email          TEXT NOT NULL UNIQUE COLLATE NOCASE,
  password_hash  TEXT NOT NULL,               -- werkzeug hash, never plaintext
  role           TEXT NOT NULL DEFAULT 'parent' CHECK (role IN ('parent','admin')),
  is_member      INTEGER NOT NULL DEFAULT 0,  -- drives member vs non-member pricing
  email_verified INTEGER NOT NULL DEFAULT 0,
  created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Children belong to a parent. Minimal PII on minors by design:
-- first name + birth year + optional UTR. No school, no address, no photos.
CREATE TABLE IF NOT EXISTS children (
  id         INTEGER PRIMARY KEY,
  parent_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name       TEXT NOT NULL,
  birth_year INTEGER,
  utr        REAL,                            -- nullable: beginners have no UTR
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- A program is the marketing unit ("High Performance").
CREATE TABLE IF NOT EXISTS programs (
  id          INTEGER PRIMARY KEY,
  name        TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  min_age     INTEGER,
  max_age     INTEGER,
  utr_min     REAL,
  utr_max     REAL,
  active      INTEGER NOT NULL DEFAULT 1,     -- soft-delete: admin hides, never loses history
  sort_order  INTEGER NOT NULL DEFAULT 0
);

-- An option is the purchasable unit ("2 days/week, $139 member").
-- Prices are INTEGER CENTS — floats lose pennies; Stripe also works in cents.
CREATE TABLE IF NOT EXISTS program_options (
  id                    INTEGER PRIMARY KEY,
  program_id            INTEGER NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
  label                 TEXT NOT NULL,
  days_per_week         INTEGER,
  billing_period        TEXT NOT NULL DEFAULT 'session' CHECK (billing_period IN ('session','week')),
  price_member_cents    INTEGER NOT NULL,
  price_nonmember_cents INTEGER NOT NULL,
  capacity              INTEGER,              -- NULL = unlimited; enforced in Phase 3
  active                INTEGER NOT NULL DEFAULT 1
);

-- An enrollment = child X option. amount_cents is COPIED at enrollment time
-- so later price changes never alter what someone already agreed to pay.
CREATE TABLE IF NOT EXISTS enrollments (
  id                INTEGER PRIMARY KEY,
  child_id          INTEGER NOT NULL REFERENCES children(id) ON DELETE CASCADE,
  option_id         INTEGER NOT NULL REFERENCES program_options(id),
  status            TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','paid','canceled')),
  amount_cents      INTEGER NOT NULL,
  stripe_session_id TEXT,                     -- set in Phase 5
  created_at        TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (child_id, option_id)                -- no double enrollment
);

-- Payment audit trail, written ONLY by the verified Stripe webhook (Phase 5).
CREATE TABLE IF NOT EXISTS payments (
  id                       INTEGER PRIMARY KEY,
  enrollment_id            INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
  stripe_payment_intent_id TEXT,
  amount_cents             INTEGER NOT NULL,
  currency                 TEXT NOT NULL DEFAULT 'usd',
  status                   TEXT NOT NULL,
  created_at               TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_children_parent   ON children(parent_id);
CREATE INDEX IF NOT EXISTS idx_options_program   ON program_options(program_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_child ON enrollments(child_id);

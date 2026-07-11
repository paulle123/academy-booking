# Academy Booking

White-label booking & enrollment system for a tennis academy. Parents register,
add their children, enroll them into programs and pay online (Stripe test mode);
the academy owner manages everything from an admin panel.

**Stack:** Flask · raw SQLite (parameterized SQL) · Jinja2 · Docker · Stripe hosted Checkout

> Project status: **Phase 1 of 7 complete** — runnable skeleton with full schema,
> seeded demo data and a public programs page. See `ROADMAP.md`.

## Run locally

```bash
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                # then set SECRET_KEY
flask --app app init-db
flask --app app seed-db
python run.py                       # http://127.0.0.1:5000
```

## Run in Docker

```bash
docker build -t academy-booking .
docker run -p 8000:8000 -e SECRET_KEY=change-me academy-booking
# http://localhost:8000  (DB inits and seeds itself on boot)
```

## Demo accounts (seeded)

| Role   | Email             | Password   |
|--------|-------------------|------------|
| Parent | parent@demo.test  | Demo1234!  |
| Admin  | admin@demo.test   | Admin1234! |

Stripe test card (once Phase 5 lands): `4242 4242 4242 4242`, any future expiry, any CVC/ZIP.

## Documentation

- `PROJECT.md` — full context brief (architecture, decisions, handoff for AI assistants)
- `ROADMAP.md` — Phases 2–7 specs with definitions of done
- `MENTOR_NOTES.md` — core concepts explained for interview defense
- `INTERVIEW_PREP.md` — likely interview questions + strong answers
- `CONTINUE_WITH_AI.md` — compressed primer + daily AI-mentor workflow

# Academy Booking

White-label booking & enrollment system for a tennis academy. Parents register,
add their children, enroll them into programs and pay online (Stripe test mode);
the academy owner manages everything from an admin panel.

**Stack:** Flask · raw SQLite (parameterized SQL) · Jinja2 · Docker · Stripe hosted Checkout

> **Live:** https://academy-booking.fly.dev — deployed on Fly.io.
> Status: Phases 1–3 (skeleton, accounts, enrollment) are the current MVP.
> Payments (Stripe) and full admin are in progress — see `ROADMAP.md`.

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

## Deploy (Fly.io)

Deployed on Fly.io with the SQLite database on a persistent volume
(survives redeploys) and `SECRET_KEY` stored as a Fly secret.

    fly deploy

Health check at `/healthz`. The machine sleeps when idle and wakes on
the next request.

## Demo accounts (seeded)

| Role   | Email             | Password   |
|--------|-------------------|------------|
| Parent | parent@demo.test  | Demo1234!  |
| Admin  | admin@demo.test   | Admin1234! |

Stripe test card (once Phase 5 lands): `4242 4242 4242 4242`, any future expiry, any CVC/ZIP.

## Documentation

- `PROJECT.md` — full context brief (architecture, decisions, handoff for AI assistants)
- `ROADMAP.md` — Phases 2–7 specs with definitions of done

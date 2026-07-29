# Academy Booking

White-label booking & enrollment system for a tennis academy. Parents register,
add their children, enroll them into programs. Payments and admin panel are planned (see status below).

**Stack:** Flask · raw SQLite (parameterized SQL) · Jinja2 · Docker · Stripe hosted Checkout

> **Live:** https://academy-booking.fly.dev — deployed on Fly.io.
>
> Status: Working MVP — parents can register, log in, log out, manage their children and enroll them into programs.
>
> Payments (Stripe) and full admin are in progress — see `ROADMAP.md`.

## What works

- Parent registration and login (hashed passwords, session auth)
- Add / edit / delete children (with ownership checks)
- Browse programs, enroll a child, view enrollments
- Deployed on Fly.io with a persistent SQLite volume

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

Stripe test card (when payments are added): `4242 4242 4242 4242`, any future expiry, any CVC/ZIP.

## Documentation

- `PROJECT.md` — full context brief (architecture, decisions, handoff for AI assistants)
- `ROADMAP.md` — Phases 2–7 specs with definitions of done

# SmartSupport — IT Expert System (Django)

## Setup
1. Create virtualenv:

2. Add `support_app` to `INSTALLED_APPS` in settings.py and configure staticfiles.

3. Run migrations:

4. Collect static (for production) or ensure `staticfiles` works in dev.

5. Run server:

6. Visit: `http://127.0.0.1:8000/support/diagnose/`

## How it works
- Fill form fields or paste JSON into the Advanced box (structured facts).
- The rule engine matches facts against 100 rules and returns ranked diagnoses with remedies.
- Cases are logged to DB for later analysis.

## Extend rules
- Edit `support_app/expert_engine.py` RULES list — add/modify rule dicts.


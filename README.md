# SpendWise — expense tracker web app

A Flask + SQLite personal expense tracker: register, log in, record expenses
(full create / read / update / delete), filter by month and category, and see
spending analytics by category and month.

> Portfolio demo. Sample data only.

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5002**. The SQLite database (`spendwise.db`) is created
automatically on first run.

## Features
- **Auth** — register / log in; passwords hashed with Werkzeug.
- **CRUD** — add, edit, and delete expenses (amount, category, note, date).
- **Filtering** — by month and category on the dashboard.
- **Analytics** — total spent, average per month, and breakdowns by category
  and by month (pure-CSS bars, no chart library).
- **Per-user data**, sessions, and CSRF-protected forms.

## Files
```
expensetracker/
├── app.py              # routes, SQLite, auth, CRUD, analytics
├── templates/          # base, index, dashboard, edit, analytics
├── static/css/style.css
├── requirements.txt
├── wsgi_pythonanywhere.py
└── spendwise.db        # auto-created (git-ignored)
```

## Deploying
Same process as the bank app — see `../bankapp/DEPLOY.md`. Upload the folder to
PythonAnywhere, point the WSGI file at it (use `wsgi_pythonanywhere.py` as a
template), set `SECRET_KEY`, and Reload.

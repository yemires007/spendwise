# Hosting SpendWise on Render (free)

Render's free tier lets you host **multiple** web apps, so this won't touch your
PythonAnywhere bank app — and you can deploy more apps the same way later.

Prerequisite: the code must be on GitHub first (see steps at the bottom).

---

## A. Deploy (the easy way — Blueprint)

This repo includes a `render.yaml`, so Render can configure everything itself.

1. Go to **https://render.com** → sign up (you can **Sign in with GitHub** — no
   credit card needed).
2. Click **New +** (top right) → **Blueprint**.
3. **Connect** your GitHub account and pick the **`spendwise`** repo.
4. Render reads `render.yaml` and shows a `spendwise` web service → click
   **Apply** / **Create**.
5. Wait ~2–3 minutes for the first build. When it's done you get a URL like
   **`https://spendwise.onrender.com`** (the name may have a suffix if taken).

`SECRET_KEY` is generated automatically by the Blueprint — nothing to set.

## B. Deploy (manual, if you skip the Blueprint)

1. **New +** → **Web Service** → connect the `spendwise` repo.
2. Settings:
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
3. **Environment** → add variable **`SECRET_KEY`** = a long random string
   (generate: `python -c "import secrets; print(secrets.token_urlsafe(48))"`).
4. **Create Web Service**.

---

## Two things to know about Render free

- **It sleeps after ~15 min of inactivity.** The first visit after that takes
  ~30–60s to wake up (you'll see a loading delay), then it's fast. Fine for a
  portfolio demo.
- **Data is not permanent.** The SQLite file lives on an ephemeral disk, so
  accounts/expenses reset whenever Render redeploys or the app restarts. That's
  fine for a demo with sample data. (Permanent storage needs a paid disk or an
  external database — ask me if you ever want that.)

## After it's live
Tell me the URL and I'll set the expense tracker's **Live demo** link in the
portfolio (`data.py`) to it.

---

## First: get the code on GitHub
```bash
cd d:/portfolio/demos/expensetracker
# create an empty repo named "spendwise" on github.com first, then:
git remote add origin https://github.com/yemires007/spendwise.git
git push -u origin main
```
(If `git remote add` says origin exists, use
`git remote set-url origin https://github.com/yemires007/spendwise.git`.)

## Hosting your other apps later
Same flow: push the app to its own GitHub repo, then on Render **New +** →
**Web Service** (or Blueprint if it has a `render.yaml`). The bank app could
live here too if you ever want it off PythonAnywhere.

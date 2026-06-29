"""
SpendWise — a personal expense tracker.

A Flask + SQLite app: register, log in, record expenses (full create / read /
update / delete), filter them, and see spending analytics by category and month.
Companion to the NaijaBank demo and built the same way:

  * Passwords hashed with Werkzeug (never stored in plain text).
  * Per-user data, sessions, and CSRF-protected forms.
  * SQLite — zero setup, deploys anywhere.

Run locally:
    python app.py        # http://127.0.0.1:5002
"""
import os
import sqlite3
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from flask import (
    Flask, flash, g, redirect, render_template, request, session, url_for,
)
from flask_wtf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "spendwise.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-spendwise-key")
csrf = CSRFProtect(app)

CATEGORIES = [
    "Food", "Transport", "Housing", "Utilities", "Health", "Entertainment",
    "Shopping", "Education", "Savings", "Other",
]


# --------------------------------------------------------------------------- #
# Database
# --------------------------------------------------------------------------- #
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                username   TEXT NOT NULL UNIQUE,
                pwd_hash   TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS expenses (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                amount     REAL NOT NULL,
                category   TEXT NOT NULL,
                note       TEXT NOT NULL DEFAULT '',
                spent_on   TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """
        )


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def now_iso():
    return datetime.now(timezone.utc).isoformat()


def today():
    return datetime.now().strftime("%Y-%m-%d")


def current_user():
    uid = session.get("user_id")
    if uid is None:
        return None
    return get_db().execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            flash("Please log in first.", "error")
            return redirect(url_for("index"))
        return view(*args, **kwargs)
    return wrapped


def valid_date(s):
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


@app.context_processor
def inject_globals():
    return {"categories": CATEGORIES, "user": current_user()}


@app.template_filter("naira")
def naira(value):
    try:
        return "₦{:,.2f}".format(float(value))
    except (TypeError, ValueError):
        return "₦0.00"


@app.template_filter("nice_date")
def nice_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d %b %Y")
    except (ValueError, TypeError):
        return value


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
@app.route("/")
def index():
    if current_user():
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["POST"])
def register():
    db = get_db()
    f = request.form
    name = f.get("name", "").strip()
    username = f.get("username", "").strip()
    pwd = f.get("password", "")
    confirm = f.get("confirm", "")

    if not name:
        flash("Please enter your name.", "error")
    elif len(username) < 3:
        flash("Username must be at least 3 characters.", "error")
    elif len(pwd) < 6:
        flash("Password must be at least 6 characters.", "error")
    elif pwd != confirm:
        flash("Passwords do not match.", "error")
    elif db.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone():
        flash("That username is already taken.", "error")
    else:
        db.execute(
            "INSERT INTO users (name, username, pwd_hash, created_at) VALUES (?,?,?,?)",
            (name, username, generate_password_hash(pwd), now_iso()),
        )
        db.commit()
        flash("Account created — please log in.", "success")
        return redirect(url_for("index"))
    return render_template("index.html", reg=f), 400


@app.route("/login", methods=["POST"])
def login():
    db = get_db()
    username = request.form.get("username", "").strip()
    pwd = request.form.get("password", "")
    row = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if row and check_password_hash(row["pwd_hash"], pwd):
        session.clear()
        session["user_id"] = row["id"]
        flash(f"Welcome back, {row['name']}.", "success")
        return redirect(url_for("dashboard"))
    flash("Invalid username or password.", "error")
    return render_template("index.html"), 400


@app.route("/logout")
def logout():
    session.clear()
    flash("You've been logged out.", "success")
    return redirect(url_for("index"))


# --------------------------------------------------------------------------- #
# Expenses (CRUD)
# --------------------------------------------------------------------------- #
@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    user = current_user()
    month = request.args.get("month", "")
    category = request.args.get("category", "")

    query = "SELECT * FROM expenses WHERE user_id=?"
    params = [user["id"]]
    if month:
        query += " AND substr(spent_on,1,7)=?"
        params.append(month)
    if category:
        query += " AND category=?"
        params.append(category)
    query += " ORDER BY spent_on DESC, id DESC"
    rows = db.execute(query, params).fetchall()

    # current-month summary (independent of the filter)
    this_month = datetime.now().strftime("%Y-%m")
    month_rows = db.execute(
        "SELECT amount, category FROM expenses WHERE user_id=? AND substr(spent_on,1,7)=?",
        (user["id"], this_month),
    ).fetchall()
    month_total = sum(r["amount"] for r in month_rows)
    all_total = db.execute(
        "SELECT COALESCE(SUM(amount),0) t FROM expenses WHERE user_id=?", (user["id"],)
    ).fetchone()["t"]
    top_cat = "—"
    if month_rows:
        by_cat = {}
        for r in month_rows:
            by_cat[r["category"]] = by_cat.get(r["category"], 0) + r["amount"]
        top_cat = max(by_cat, key=by_cat.get)

    months = [r["m"] for r in db.execute(
        "SELECT DISTINCT substr(spent_on,1,7) m FROM expenses WHERE user_id=? "
        "ORDER BY m DESC", (user["id"],)
    ).fetchall()]

    filtered_total = sum(r["amount"] for r in rows)

    return render_template(
        "dashboard.html",
        expenses=rows,
        today=today(),
        month_total=month_total,
        month_count=len(month_rows),
        all_total=all_total,
        top_cat=top_cat,
        months=months,
        sel_month=month,
        sel_category=category,
        filtered_total=filtered_total,
    )


def _parse_expense_form(f):
    """Return (data, error). data is a dict ready for the DB."""
    try:
        amount = float(f.get("amount", ""))
    except ValueError:
        amount = -1
    category = f.get("category", "")
    note = f.get("note", "").strip()[:200]
    spent_on = f.get("spent_on", "") or today()

    if amount <= 0:
        return None, "Enter an amount greater than zero."
    if category not in CATEGORIES:
        return None, "Pick a valid category."
    if not valid_date(spent_on):
        return None, "Enter a valid date."
    return {"amount": amount, "category": category, "note": note,
            "spent_on": spent_on}, None


@app.route("/expense/add", methods=["POST"])
@login_required
def add_expense():
    db = get_db()
    user = current_user()
    data, err = _parse_expense_form(request.form)
    if err:
        flash(err, "error")
    else:
        db.execute(
            "INSERT INTO expenses (user_id, amount, category, note, spent_on, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (user["id"], data["amount"], data["category"], data["note"],
             data["spent_on"], now_iso()),
        )
        db.commit()
        flash(f"Added {naira(data['amount'])} for {data['category']}.", "success")
    return redirect(url_for("dashboard"))


def _owned_expense(expense_id):
    user = current_user()
    return get_db().execute(
        "SELECT * FROM expenses WHERE id=? AND user_id=?", (expense_id, user["id"])
    ).fetchone()


@app.route("/expense/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    exp = _owned_expense(expense_id)
    if exp is None:
        flash("Expense not found.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "GET":
        return render_template("edit.html", exp=exp, today=today())

    data, err = _parse_expense_form(request.form)
    if err:
        flash(err, "error")
        return render_template("edit.html", exp=exp, today=today()), 400
    get_db().execute(
        "UPDATE expenses SET amount=?, category=?, note=?, spent_on=? WHERE id=?",
        (data["amount"], data["category"], data["note"], data["spent_on"], expense_id),
    )
    get_db().commit()
    flash("Expense updated.", "success")
    return redirect(url_for("dashboard"))


@app.route("/expense/<int:expense_id>/delete", methods=["POST"])
@login_required
def delete_expense(expense_id):
    exp = _owned_expense(expense_id)
    if exp is None:
        flash("Expense not found.", "error")
    else:
        get_db().execute("DELETE FROM expenses WHERE id=?", (expense_id,))
        get_db().commit()
        flash("Expense deleted.", "success")
    return redirect(url_for("dashboard"))


# --------------------------------------------------------------------------- #
# Analytics
# --------------------------------------------------------------------------- #
def _bars(totals):
    top = max(totals.values(), default=0) or 1
    return [
        {"label": k, "amount": v, "pct": round(v / top * 100)}
        for k, v in sorted(totals.items(), key=lambda kv: -kv[1])
    ]


@app.route("/analytics")
@login_required
def analytics():
    db = get_db()
    user = current_user()
    rows = db.execute(
        "SELECT amount, category, spent_on FROM expenses WHERE user_id=?", (user["id"],)
    ).fetchall()

    total = sum(r["amount"] for r in rows)
    by_cat, monthly = {}, {}
    for r in rows:
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + r["amount"]
        ym = r["spent_on"][:7]
        monthly[ym] = monthly.get(ym, 0) + r["amount"]

    month_top = max(monthly.values(), default=0) or 1
    monthly_rows = []
    for ym, amt in sorted(monthly.items()):
        try:
            label = datetime.strptime(ym, "%Y-%m").strftime("%b %Y")
        except ValueError:
            label = ym
        monthly_rows.append({"month": label, "amount": amt,
                             "pct": round(amt / month_top * 100)})

    avg_month = (total / len(monthly)) if monthly else 0

    return render_template(
        "analytics.html",
        count=len(rows),
        total=total,
        avg_month=avg_month,
        by_cat=_bars(by_cat),
        monthly=monthly_rows,
    )


init_db()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(debug=debug, port=5002)

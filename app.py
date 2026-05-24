from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import json
import os
from datetime import datetime, date
import calendar
import csv
import io

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")

CATEGORIES = {
    "food": {"name": "Хоол, хүнс", "icon": "🍜"},
    "transport": {"name": "Тээвэр", "icon": "🚌"},
    "shopping": {"name": "Дэлгүүр", "icon": "🛍️"},
    "health": {"name": "Эрүүл мэнд", "icon": "💊"},
    "education": {"name": "Боловсрол", "icon": "📚"},
    "entertainment": {"name": "Цэнгэл", "icon": "🎮"},
    "bills": {"name": "Тооцоо, утас", "icon": "📱"},
    "savings": {"name": "Хадгаламж", "icon": "💰"},
    "other": {"name": "Бусад", "icon": "📦"},
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL CHECK(type IN ('expense', 'income')),
            amount INTEGER NOT NULL,
            category TEXT NOT NULL,
            note TEXT,
            date TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            month TEXT NOT NULL,
            limit_amount INTEGER NOT NULL,
            UNIQUE(category, month)
        );
    """)
    conn.commit()
    conn.close()

def ai_advice(stats, month_label):
    top_cat = max(stats["by_category"].items(), key=lambda x: x[1], default=(None, 0))
    balance = stats["income"] - stats["expense"]
    save_rate = (balance / stats["income"] * 100) if stats["income"] > 0 else 0

    advices = []

    if stats["income"] == 0:
        advices.append({"type": "info", "text": "Энэ сард орлого бүртгэгдээгүй байна. Орлогоо бүртгэснээр дүн шинжилгээ илүү нарийн гарна."})
    elif save_rate < 10:
        advices.append({"type": "danger", "text": f"Орлогынхоо зөвхөн {save_rate:.0f}%-г хэмнэж байна. Санхүүгийн зөвлөгөөч нар орлогын 20%-г хэмнэхийг зөвлөдөг."})
    elif save_rate < 20:
        advices.append({"type": "warning", "text": f"Орлогынхоо {save_rate:.0f}%-г хэмнэж байна. Бага ч гэсэн сайн. 20% хүртэл нэмэхийг хичээгээрэй."})
    else:
        advices.append({"type": "success", "text": f"Орлогынхоо {save_rate:.0f}%-г хэмнэж байна. Маш сайн! Энэ хэмжээг хадгалаарай."})

    if top_cat[0]:
        cat_name = CATEGORIES.get(top_cat[0], {}).get("name", top_cat[0])
        advices.append({"type": "info", "text": f"Хамгийн их зарлага '{cat_name}' ангилалд байна — {top_cat[1]:,}₮. Энэ ангилалд зорилго тавьж үзээрэй."})

    if stats["expense"] > 0 and stats["income"] > 0:
        daily_avg = stats["expense"] / datetime.now().day
        remaining_days = calendar.monthrange(datetime.now().year, datetime.now().month)[1] - datetime.now().day
        projected = stats["expense"] + (daily_avg * remaining_days)
        if projected > stats["income"]:
            advices.append({"type": "danger", "text": f"Одоогийн хэмжээгээр сарын эцэст зарлага {projected:,.0f}₮ болж орлогоос давна. Анхаарна уу!"})

    if balance > 0:
        yearly = balance * 12
        advices.append({"type": "success", "text": f"Энэ хэмжээний хэмнэлтээр жилд {yearly:,}₮ хуримтлуулах боломжтой."})

    return advices

@app.route("/")
def index():
    return render_template("index.html", categories=CATEGORIES)

@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM transactions WHERE date LIKE ? ORDER BY date DESC, created_at DESC",
        (f"{month}%",)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/transactions", methods=["POST"])
def add_transaction():
    data = request.json
    required = ["type", "amount", "category", "date"]
    for f in required:
        if not data.get(f):
            return jsonify({"error": f"{f} талбар шаардлагатай"}), 400
    try:
        amount = int(str(data["amount"]).replace(",", "").replace(" ", ""))
        if amount <= 0:
            raise ValueError
    except:
        return jsonify({"error": "Дүн зөв оруулна уу"}), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO transactions (type, amount, category, note, date, created_at) VALUES (?,?,?,?,?,?)",
        (data["type"], amount, data["category"], data.get("note", ""), data["date"], datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/transactions/<int:tid>", methods=["DELETE"])
def delete_transaction(tid):
    conn = get_db()
    conn.execute("DELETE FROM transactions WHERE id=?", (tid,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/stats", methods=["GET"])
def get_stats():
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    conn = get_db()

    rows = conn.execute(
        "SELECT * FROM transactions WHERE date LIKE ?", (f"{month}%",)
    ).fetchall()

    income = sum(r["amount"] for r in rows if r["type"] == "income")
    expense = sum(r["amount"] for r in rows if r["type"] == "expense")

    by_category = {}
    for r in rows:
        if r["type"] == "expense":
            by_category[r["category"]] = by_category.get(r["category"], 0) + r["amount"]

    daily = {}
    for r in rows:
        d = r["date"]
        if d not in daily:
            daily[d] = {"income": 0, "expense": 0}
        daily[d][r["type"]] += r["amount"]

    goals = conn.execute("SELECT * FROM goals WHERE month=?", (month,)).fetchall()
    goals_data = {g["category"]: g["limit_amount"] for g in goals}

    conn.close()

    stats = {"income": income, "expense": expense, "by_category": by_category, "daily": daily}
    advices = ai_advice(stats, month)

    return jsonify({
        "income": income,
        "expense": expense,
        "balance": income - expense,
        "by_category": by_category,
        "daily": daily,
        "goals": goals_data,
        "advices": advices,
    })

@app.route("/api/yearly", methods=["GET"])
def get_yearly():
    year = request.args.get("year", str(datetime.now().year))
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM transactions WHERE date LIKE ?", (f"{year}%",)
    ).fetchall()
    conn.close()

    monthly = {}
    by_category_year = {}
    for r in rows:
        m = r["date"][:7]
        if m not in monthly:
            monthly[m] = {"income": 0, "expense": 0}
        monthly[m][r["type"]] += r["amount"]
        if r["type"] == "expense":
            by_category_year[r["category"]] = by_category_year.get(r["category"], 0) + r["amount"]

    total_income = sum(r["amount"] for r in rows if r["type"] == "income")
    total_expense = sum(r["amount"] for r in rows if r["type"] == "expense")

    yearly_advices = []
    if by_category_year:
        top = max(by_category_year.items(), key=lambda x: x[1])
        cat_name = CATEGORIES.get(top[0], {}).get("name", top[0])
        pct = top[1] / total_expense * 100 if total_expense else 0
        yearly_advices.append({"type": "info", "text": f"Жилд хамгийн их зарлага '{cat_name}'-д — {top[1]:,}₮ ({pct:.0f}%)"})
    if total_income > 0:
        save = (total_income - total_expense) / total_income * 100
        yearly_advices.append({"type": "success" if save >= 20 else "warning", "text": f"Жилийн хэмнэлтийн хувь: {save:.1f}%"})

    return jsonify({
        "monthly": monthly,
        "by_category": by_category_year,
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense,
        "advices": yearly_advices,
    })

@app.route("/api/goals", methods=["POST"])
def set_goal():
    data = request.json
    month = data.get("month", datetime.now().strftime("%Y-%m"))
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO goals (category, month, limit_amount) VALUES (?,?,?)",
        (data["category"], month, int(data["limit_amount"]))
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/export/csv", methods=["GET"])
def export_csv():
    month = request.args.get("month", "")
    conn = get_db()
    if month:
        rows = conn.execute("SELECT * FROM transactions WHERE date LIKE ? ORDER BY date", (f"{month}%",)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM transactions ORDER BY date").fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Огноо", "Төрөл", "Ангилал", "Дүн", "Тэмдэглэл"])
    for r in rows:
        cat_name = CATEGORIES.get(r["category"], {}).get("name", r["category"])
        t = "Орлого" if r["type"] == "income" else "Зарлага"
        writer.writerow([r["date"], t, cat_name, r["amount"], r["note"] or ""])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"zarlagaa_{month or 'bugd'}.csv"
    )

if __name__ == "__main__":
    init_db()
    print("\n✅ Апп эхэллээ! Browser дээр: http://localhost:5000\n")
    app.run(debug=False, host="0.0.0.0", port=5000)

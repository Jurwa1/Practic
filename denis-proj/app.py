import sqlite3
from datetime import date
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, url_for

app = Flask(__name__)

DB_PATH = Path(__file__).resolve().parent / "inventory.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

STATUS_LABELS = {
    "working": "Работает",
    "in_stock": "На складе",
    "broken": "Сломан",
    "decommissioned": "Списан",
}

DEVICE_TYPES = ["Компьютер", "Монитор", "Принтер", "МФУ", "Ноутбук"]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    if DB_PATH.exists():
        return
    conn = get_connection()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


init_db()


# ---------- Главная: список техники ----------

@app.route("/")
def equipment_list():
    query = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()

    sql = """
        SELECT e.*, r.room_number, r.floor, emp.full_name AS employee_name
        FROM equipment e
        LEFT JOIN rooms r ON e.room_id = r.id
        LEFT JOIN employees emp ON e.employee_id = emp.id
        WHERE 1 = 1
    """
    params = []
    if query:
        sql += " AND (e.inventory_number LIKE ? OR e.device_type LIKE ? OR e.model LIKE ?)"
        like = f"%{query}%"
        params += [like, like, like]
    if status:
        sql += " AND e.status = ?"
        params.append(status)
    sql += " ORDER BY e.id DESC"

    conn = get_connection()
    devices = conn.execute(sql, params).fetchall()

    return render_template(
        "equipment_list.html",
        active="equipment",
        devices=devices,
        statuses=STATUS_LABELS,
        query=query,
        status=status,
    )


@app.route("/equipment/new", methods=["GET", "POST"])
def equipment_new():
    conn = get_connection()

    if request.method == "POST":
        conn.execute(
            """INSERT INTO equipment
               (inventory_number, device_type, model, specs, room_id, employee_id, ip_address, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                request.form["inventory_number"].strip(),
                request.form["device_type"],
                request.form.get("model", "").strip() or None,
                request.form.get("specs", "").strip() or None,
                request.form.get("room_id") or None,
                request.form.get("employee_id") or None,
                request.form.get("ip_address", "").strip() or None,
                request.form.get("status", "in_stock"),
            ),
        )
        conn.commit()
        return redirect(url_for("equipment_list"))

    rooms = conn.execute("SELECT * FROM rooms ORDER BY floor, room_number").fetchall()
    employees = conn.execute("SELECT * FROM employees ORDER BY full_name").fetchall()
    return render_template(
        "equipment_form.html",
        active="equipment",
        device=None,
        statuses=STATUS_LABELS,
        device_types=DEVICE_TYPES,
        rooms=rooms,
        employees=employees,
    )


@app.route("/equipment/<int:equipment_id>/edit", methods=["GET", "POST"])
def equipment_edit(equipment_id):
    conn = get_connection()

    if request.method == "POST":
        conn.execute(
            """UPDATE equipment SET
               inventory_number = ?, device_type = ?, model = ?, specs = ?,
               room_id = ?, employee_id = ?, ip_address = ?, status = ?
               WHERE id = ?""",
            (
                request.form["inventory_number"].strip(),
                request.form["device_type"],
                request.form.get("model", "").strip() or None,
                request.form.get("specs", "").strip() or None,
                request.form.get("room_id") or None,
                request.form.get("employee_id") or None,
                request.form.get("ip_address", "").strip() or None,
                request.form.get("status", "in_stock"),
                equipment_id,
            ),
        )
        conn.commit()
        return redirect(url_for("equipment_list"))

    device = conn.execute("SELECT * FROM equipment WHERE id = ?", (equipment_id,)).fetchone()
    if device is None:
        abort(404)
    rooms = conn.execute("SELECT * FROM rooms ORDER BY floor, room_number").fetchall()
    employees = conn.execute("SELECT * FROM employees ORDER BY full_name").fetchall()
    return render_template(
        "equipment_form.html",
        active="equipment",
        device=device,
        statuses=STATUS_LABELS,
        device_types=DEVICE_TYPES,
        rooms=rooms,
        employees=employees,
    )


@app.route("/equipment/<int:equipment_id>/delete", methods=["POST"])
def equipment_delete(equipment_id):
    conn = get_connection()
    conn.execute("DELETE FROM equipment WHERE id = ?", (equipment_id,))
    conn.commit()
    return redirect(url_for("equipment_list"))


# ---------- Карточка устройства ----------

@app.route("/equipment/<int:equipment_id>")
def equipment_detail(equipment_id):
    conn = get_connection()
    device = conn.execute(
        """
        SELECT e.*, r.room_number, r.floor, emp.full_name AS employee_name
        FROM equipment e
        LEFT JOIN rooms r ON e.room_id = r.id
        LEFT JOIN employees emp ON e.employee_id = emp.id
        WHERE e.id = ?
        """,
        (equipment_id,),
    ).fetchone()
    if device is None:
        abort(404)

    repairs = conn.execute(
        "SELECT * FROM repairs WHERE equipment_id = ? ORDER BY repair_date DESC, id DESC",
        (equipment_id,),
    ).fetchall()

    return render_template(
        "equipment_detail.html",
        active="equipment",
        device=device,
        repairs=repairs,
        statuses=STATUS_LABELS,
    )


@app.route("/equipment/<int:equipment_id>/repairs", methods=["POST"])
def equipment_add_repair(equipment_id):
    conn = get_connection()
    conn.execute(
        "INSERT INTO repairs (equipment_id, repair_date, admin_name, description) VALUES (?, ?, ?, ?)",
        (equipment_id, date.today().isoformat(), request.form["admin_name"].strip(), request.form["description"].strip()),
    )
    conn.commit()
    return redirect(url_for("equipment_detail", equipment_id=equipment_id))


# ---------- Склад ----------

@app.route("/warehouse")
def warehouse():
    conn = get_connection()
    items = conn.execute("SELECT * FROM warehouse ORDER BY category, name").fetchall()
    return render_template("warehouse.html", active="warehouse", items=items)


@app.route("/warehouse/new", methods=["POST"])
def warehouse_new():
    conn = get_connection()
    conn.execute(
        "INSERT INTO warehouse (name, category, quantity, min_threshold) VALUES (?, ?, ?, ?)",
        (
            request.form["name"].strip(),
            request.form.get("category", "").strip() or None,
            int(request.form.get("quantity") or 0),
            int(request.form.get("min_threshold") or 0),
        ),
    )
    conn.commit()
    return redirect(url_for("warehouse"))


@app.route("/warehouse/<int:item_id>/adjust", methods=["POST"])
def warehouse_adjust(item_id):
    conn = get_connection()
    delta = int(request.form.get("delta", 0))
    conn.execute(
        "UPDATE warehouse SET quantity = MAX(0, quantity + ?) WHERE id = ?",
        (delta, item_id),
    )
    conn.commit()
    return redirect(url_for("warehouse"))


# ---------- Журнал ремонтов ----------

@app.route("/repairs")
def repairs_log():
    conn = get_connection()
    entries = conn.execute(
        """
        SELECT rp.*, e.inventory_number, e.device_type, e.model
        FROM repairs rp
        JOIN equipment e ON rp.equipment_id = e.id
        ORDER BY rp.repair_date DESC, rp.id DESC
        """
    ).fetchall()
    return render_template("repairs.html", active="repairs", entries=entries)


if __name__ == "__main__":
    app.run(debug=True, port=5050)

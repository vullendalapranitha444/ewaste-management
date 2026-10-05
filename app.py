from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "ewaste_management_secret"

DATABASE = "ewaste.db"


# ================= DATABASE =================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL,
            points INTEGER DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS pickups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            waste_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            location TEXT NOT NULL,
            pickup_date TEXT NOT NULL,
            status TEXT DEFAULT 'Requested',
            points INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ================= HOME =================

@app.route("/")
def home():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# ================= REGISTER =================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]

        conn = get_db()

        try:

            conn.execute("""
                INSERT INTO users
                (name, email, phone, password)
                VALUES (?, ?, ?, ?)
            """, (name, email, phone, password))

            conn.commit()

            flash("Registration successful! Please login.")

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            flash("This email is already registered.")

        finally:

            conn.close()

    return render_template("register.html")


# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE email = ? AND password = ?
        """, (email, password)).fetchone()

        conn.close()

        if user:

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")

    return render_template("login.html")


# ================= LOGOUT =================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (session["user_id"],)).fetchone()

    total_pickups = conn.execute("""
        SELECT COUNT(*) AS total
        FROM pickups
        WHERE user_id = ?
    """, (session["user_id"],)).fetchone()["total"]

    total_waste = conn.execute("""
        SELECT COALESCE(SUM(quantity), 0) AS total
        FROM pickups
        WHERE user_id = ?
    """, (session["user_id"],)).fetchone()["total"]

    conn.close()

    return render_template(
        "dashboard.html",
        user=user,
        total_pickups=total_pickups,
        total_waste=total_waste
    )


# ================= SUBMIT E-WASTE =================

@app.route("/submit-waste", methods=["GET", "POST"])
def submit_waste():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        waste_type = request.form["waste_type"]
        quantity = int(request.form["quantity"])
        location = request.form["location"]
        pickup_date = request.form["pickup_date"]

        reward_points = {
            "Mobile Phone": 20,
            "Laptop": 50,
            "Computer": 40,
            "Television": 35,
            "Battery": 15,
            "Printer": 30,
            "Other": 10
        }

        points = reward_points.get(waste_type, 10) * quantity

        conn = get_db()

        conn.execute("""
            INSERT INTO pickups
            (
                user_id,
                waste_type,
                quantity,
                location,
                pickup_date,
                status,
                points,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            waste_type,
            quantity,
            location,
            pickup_date,
            "Requested",
            points,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.execute("""
            UPDATE users
            SET points = points + ?
            WHERE id = ?
        """, (points, session["user_id"]))

        conn.commit()
        conn.close()

        flash(
            f"Pickup request submitted successfully! "
            f"You earned {points} reward points."
        )

        return redirect(url_for("dashboard"))

    return render_template("submit_waste.html")


# ================= PICKUP =================

@app.route("/pickup")
def pickup():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    pickups = conn.execute("""
        SELECT *
        FROM pickups
        WHERE user_id = ?
        ORDER BY id DESC
    """, (session["user_id"],)).fetchall()

    conn.close()

    return render_template(
        "pickup.html",
        pickups=pickups
    )


# ================= REWARDS =================

@app.route("/rewards")
def rewards():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (session["user_id"],)).fetchone()

    conn.close()

    return render_template(
        "rewards.html",
        user=user
    )


# ================= HISTORY =================

@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    history = conn.execute("""
        SELECT *
        FROM pickups
        WHERE user_id = ?
        ORDER BY id DESC
    """, (session["user_id"],)).fetchall()

    conn.close()

    return render_template(
        "history.html",
        history=history
    )


# ================= START APPLICATION =================

if __name__ == "__main__":

    init_db()

    app.run(debug=True)
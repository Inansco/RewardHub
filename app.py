from flask import Flask, render_template, request, redirect, url_for, session
from database import init_db, get_db
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

import os

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "development-secret-key"
)

init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        connection = get_db()

        try:
            connection.execute(
                """
                INSERT INTO users (username, email, password)
                VALUES (?, ?, ?)
                """,
                (username, email, hashed_password)
            )

            connection.commit()

        except Exception:
            connection.close()
            return "Username or email already exists."

        connection.close()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db()

        user = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        connection.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]

            return redirect(url_for("dashboard"))

        return "Invalid email or password."

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    user = connection.execute(
        """
        SELECT * FROM users
        WHERE id = ?
        """,
        (session["user_id"],)
    ).fetchone()

    transactions = connection.execute(
        """
        SELECT * FROM transactions
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 10
        """,
        (session["user_id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "dashboard.html",
        user=user,
        transactions=transactions
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))



@app.route("/earn")
def earn():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    tasks = connection.execute(
        """
        SELECT * FROM tasks
        WHERE active = 1
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return render_template("earn.html", tasks=tasks)



@app.route("/complete-task/<int:task_id>")
def complete_task(task_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db()

    # Find the task
    task = connection.execute(
        """
        SELECT * FROM tasks
        WHERE id = ? AND active = 1
        """,
        (task_id,)
    ).fetchone()

    if not task:
        connection.close()
        return "Task not found."

    # Check whether the user already completed it
    completed = connection.execute(
        """
        SELECT * FROM completed_tasks
        WHERE user_id = ? AND task_id = ?
        """,
        (user_id, task_id)
    ).fetchone()

    if completed:
        connection.close()
        return "You have already completed this task."

    # Add points to user
    connection.execute(
        """
        UPDATE users
        SET points = points + ?
        WHERE id = ?
        """,
        (task["points"], user_id)
    )

    # Record transaction
    connection.execute(
        """
        INSERT INTO transactions
        (user_id, points, description)
        VALUES (?, ?, ?)
        """,
        (
            user_id,
            task["points"],
            f"Completed task: {task['title']}"
        )
    )

    # Mark task as completed
    connection.execute(
        """
        INSERT INTO completed_tasks
        (user_id, task_id)
        VALUES (?, ?)
        """,
        (user_id, task_id)
    )

@app.route("/rewards")
def rewards():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    user = connection.execute(
        """
        SELECT * FROM users
        WHERE id = ?
        """,
        (session["user_id"],)
    ).fetchone()

    rewards = connection.execute(
        """
        SELECT * FROM rewards
        WHERE active = 1
        ORDER BY points_required ASC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "rewards.html",
        user=user,
        rewards=rewards
    )

@app.route("/redeem/<int:reward_id>")
def redeem(reward_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db()

    user = connection.execute(
        """
        SELECT * FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    reward = connection.execute(
        """
        SELECT * FROM rewards
        WHERE id = ? AND active = 1
        """,
        (reward_id,)
    ).fetchone()

    if not reward:
        connection.close()
        return "Reward not found."

    if user["points"] < reward["points_required"]:
        connection.close()
        return "You do not have enough points."

    # Deduct points
    connection.execute(
        """
        UPDATE users
        SET points = points - ?
        WHERE id = ?
        """,
        (reward["points_required"], user_id)
    )

    # Create withdrawal
    connection.execute(
        """
        INSERT INTO withdrawals
        (
            user_id,
            reward_id,
            points_spent,
            cash_value
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            reward["id"],
            reward["points_required"],
            reward["cash_value"]
        )
    )

    # Record transaction
    connection.execute(
        """
        INSERT INTO transactions
        (
            user_id,
            points,
            description
        )
        VALUES (?, ?, ?)
        """,
        (
            user_id,
            -reward["points_required"],
            f"Redeemed: {reward['name']}"
        )
    )

@app.route("/withdrawals")
def withdrawals():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db()

    withdrawals = connection.execute(
        """
        SELECT
            withdrawals.*,
            rewards.name AS reward_name
        FROM withdrawals
        JOIN rewards
            ON withdrawals.reward_id = rewards.id
        WHERE withdrawals.user_id = ?
        ORDER BY withdrawals.created_at DESC
        """,
        (user_id,)
    ).fetchall()

    connection.close()

    return render_template(
        "withdrawals.html",
        withdrawals=withdrawals
    )

    connection.commit()
    connection.close()

    return redirect(url_for("dashboard"))

    connection.commit()
    connection.close()

    return redirect(url_for("dashboard"))



if __name__ == "__main__":
    app.run(debug=True)
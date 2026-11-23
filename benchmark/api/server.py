import os
import sqlite3
from flask import Flask, request, jsonify


app = Flask(__name__)

DB_PATH = os.environ.get("API_DB_PATH", "/workspace/benchmark/api/users.db")


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL
            )
        """)

        count = connection.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]

        if count == 0:
            connection.executemany(
                "INSERT INTO users (id, name, email, role) VALUES (?, ?, ?, ?)",
                [
                    (1, "Alice", "alice@example.com", "admin"),
                    (2, "Bob", "bob@example.com", "user"),
                    (3, "David", "david@example.com", "admin"),
                ],
            )


def valid_email(email):
    return (
        isinstance(email, str)
        and "@" in email
        and "." in email.split("@")[-1]
    )


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    with get_connection() as connection:
        user = connection.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()

    if user is None:
        return jsonify({"error": "User not found"}), 404

    return jsonify(dict(user)), 200


@app.route("/users", methods=["GET"])
def list_users():
    role = request.args.get("role")

    with get_connection() as connection:
        if role:
            users = connection.execute(
                "SELECT * FROM users WHERE role = ? ORDER BY id",
                (role,),
            ).fetchall()
        else:
            users = connection.execute(
                "SELECT * FROM users ORDER BY id"
            ).fetchall()

    return jsonify([dict(user) for user in users]), 200


@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json(silent=True) or {}

    name = data.get("name")
    email = data.get("email")
    role = data.get("role", "user")

    if not name or not email or not valid_email(email):
        return jsonify({"error": "Invalid name or email"}), 400

    try:
        with get_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO users (name, email, role) VALUES (?, ?, ?)",
                (name, email, role),
            )
            user_id = cursor.lastrowid

        return jsonify({"id": user_id, "name": name, "email": email, "role": role}), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 409


@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.get_json(silent=True) or {}

    name = data.get("name")
    email = data.get("email")

    if not name or not email or not valid_email(email):
        return jsonify({"error": "Invalid name or email"}), 400

    with get_connection() as connection:
        existing = connection.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()

        if existing is None:
            return jsonify({"error": "User not found"}), 404

        try:
            connection.execute(
                "UPDATE users SET name = ?, email = ? WHERE id = ?",
                (name, email, user_id),
            )
        except sqlite3.IntegrityError:
            return jsonify({"error": "Email already exists"}), 409

    return jsonify({
        "id": user_id,
        "name": name,
        "email": email,
        "role": existing["role"],
    }), 200


@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM users WHERE id = ?", (user_id,)
        )

        if cursor.rowcount == 0:
            return jsonify({"error": "User not found"}), 404

    return jsonify({"message": "User deleted"}), 200


initialize_database()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

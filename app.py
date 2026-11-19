import os
import socket
import pymysql
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

def get_db():
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
    )

def init_db():
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                "CREATE TABLE IF NOT EXISTS tasks ("
                "id INT AUTO_INCREMENT PRIMARY KEY, "
                "title VARCHAR(255) NOT NULL)"
            )
        conn.close()
    except Exception as e:
        print("DB init failed:", e)

init_db()

PAGE = """
<!doctype html>
<title>My 2-Tier App</title>
<body style="font-family:Arial;max-width:600px;margin:40px auto">
<h1>My 2-Tier App (Flask + RDS MySQL)</h1>
<p><b>Served by:</b> {{ host }}</p>
<form method="post" action="/add">
  <input name="title" placeholder="New task" required>
  <button>Add</button>
</form>
<ul>
{% for t in tasks %}
  <li>{{ t.title }} <a href="/delete/{{ t.id }}">[delete]</a></li>
{% endfor %}
</ul>
</body>
"""

@app.route("/health")
def health():
    return "OK", 200

@app.route("/")
def home():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT id, title FROM tasks ORDER BY id DESC")
        tasks = cur.fetchall()
    conn.close()
    return render_template_string(PAGE, tasks=tasks, host=socket.gethostname())

@app.route("/add", methods=["POST"])
def add():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("INSERT INTO tasks (title) VALUES (%s)", (request.form["title"],))
    conn.close()
    return redirect("/")

@app.route("/delete/<int:task_id>")
def delete(task_id):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM tasks WHERE id=%s", (task_id,))
    conn.close()
    return redirect("/")
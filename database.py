import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

# SQLite db path - stored in the project folder
# on hf spaces, /data is the persistent storage dir
DB_PATH = os.getenv('DB_PATH', os.path.join(os.path.dirname(__file__), 'agentflow.db'))


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # so we can access columns by name
    return conn


def init_db():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # main tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_text TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'running',
                final_answer TEXT,
                total_steps INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # each step the agent takes gets logged here
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                step_number INTEGER NOT NULL,
                thought TEXT,
                tool_name VARCHAR(50),
                tool_input TEXT,
                tool_output TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print("database ready!")

    except Exception as e:
        print(f"db error: {e}")


def create_task(task_text):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (task_text) VALUES (?)",
            (task_text,)
        )
        conn.commit()
        task_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return task_id
    except Exception as e:
        print(f"error creating task: {e}")
        return None


def save_step(task_id, step_number, thought, tool_name=None, tool_input=None, tool_output=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO task_steps (task_id, step_number, thought, tool_name, tool_input, tool_output) VALUES (?, ?, ?, ?, ?, ?)",
            (task_id, step_number, thought, tool_name, tool_input, tool_output)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"error saving step: {e}")


def complete_task(task_id, final_answer, total_steps):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tasks SET status = 'completed', final_answer = ?, total_steps = ? WHERE id = ?",
            (final_answer, total_steps, task_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"error completing task: {e}")


def fail_task(task_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tasks SET status = 'failed' WHERE id = ?",
            (task_id,)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"error failing task: {e}")


def get_history():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT 50")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        # convert Row objects to dicts
        results = []
        for row in rows:
            row_dict = dict(row)
            if row_dict.get('created_at'):
                row_dict['created_at'] = str(row_dict['created_at'])
            results.append(row_dict)
        return results
    except Exception as e:
        print(f"error getting history: {e}")
        return []


def get_task_steps(task_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM task_steps WHERE task_id = ? ORDER BY step_number",
            (task_id,)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        results = []
        for row in rows:
            row_dict = dict(row)
            if row_dict.get('created_at'):
                row_dict['created_at'] = str(row_dict['created_at'])
            results.append(row_dict)
        return results
    except Exception as e:
        print(f"error getting steps: {e}")
        return []

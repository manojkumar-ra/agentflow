import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DATABASE', 'agentflow')
    )
    return conn


def init_db():
    try:
        # connect without specifying db first to create it if needed
        conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', '')
        )
        cursor = conn.cursor()

        db_name = os.getenv('MYSQL_DATABASE', 'agentflow')
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cursor.execute(f"USE {db_name}")

        # main tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                task_text TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'running',
                final_answer TEXT,
                total_steps INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # each step the agent takes gets logged here
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_steps (
                id INT AUTO_INCREMENT PRIMARY KEY,
                task_id INT NOT NULL,
                step_number INT NOT NULL,
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
        print("make sure mysql is running!")


def create_task(task_text):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (task_text) VALUES (%s)",
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
            "INSERT INTO task_steps (task_id, step_number, thought, tool_name, tool_input, tool_output) VALUES (%s, %s, %s, %s, %s, %s)",
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
            "UPDATE tasks SET status = 'completed', final_answer = %s, total_steps = %s WHERE id = %s",
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
            "UPDATE tasks SET status = 'failed' WHERE id = %s",
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
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT 50")
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        for row in results:
            if row.get('created_at'):
                row['created_at'] = str(row['created_at'])
        return results
    except Exception as e:
        print(f"error getting history: {e}")
        return []


def get_task_steps(task_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM task_steps WHERE task_id = %s ORDER BY step_number",
            (task_id,)
        )
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        for row in results:
            if row.get('created_at'):
                row['created_at'] = str(row['created_at'])
        return results
    except Exception as e:
        print(f"error getting steps: {e}")
        return []

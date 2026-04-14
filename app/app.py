from flask import Flask, request, jsonify, render_template
import sqlite3
import os
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

app = Flask(__name__)
DB_PATH = "/data/tasks.db"

# --- Prometheus metrics ---
REQUEST_COUNT = Counter(
    'taskflow_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)
REQUEST_LATENCY = Histogram(
    'taskflow_request_duration_seconds',
    'Request latency in seconds',
    ['endpoint']
)

# --- Database setup ---
def get_db():
    """Connect to SQLite database."""
    os.makedirs("/data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create the tasks table if it doesn't exist."""
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

# --- Routes ---
@app.route('/')
def index():
    """Main page — renders the task list."""
    start = time.time()
    with get_db() as conn:
        tasks = conn.execute('SELECT * FROM tasks ORDER BY created_at DESC').fetchall()
    REQUEST_COUNT.labels('GET', '/', '200').inc()
    REQUEST_LATENCY.labels('/').observe(time.time() - start)
    return render_template('index.html', tasks=tasks)

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """API: return all tasks as JSON."""
    with get_db() as conn:
        tasks = conn.execute('SELECT * FROM tasks').fetchall()
    REQUEST_COUNT.labels('GET', '/api/tasks', '200').inc()
    return jsonify([dict(t) for t in tasks])

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """API: create a new task."""
    data = request.get_json()
    title = data.get('title', '').strip()
    if not title:
        REQUEST_COUNT.labels('POST', '/api/tasks', '400').inc()
        return jsonify({'error': 'Title is required'}), 400
    with get_db() as conn:
        conn.execute('INSERT INTO tasks (title) VALUES (?)', (title,))
        conn.commit()
    REQUEST_COUNT.labels('POST', '/api/tasks', '201').inc()
    return jsonify({'message': 'Task created'}), 201

@app.route('/api/tasks/<int:task_id>/done', methods=['PUT'])
def toggle_task(task_id):
    """API: toggle a task's completion status."""
    with get_db() as conn:
        conn.execute('UPDATE tasks SET done = 1 - done WHERE id = ?', (task_id,))
        conn.commit()
    REQUEST_COUNT.labels('PUT', '/api/tasks/done', '200').inc()
    return jsonify({'message': 'Task updated'})
    return jsonify({'message': 'Task updated'})

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """API: delete a task."""
    with get_db() as conn:
        conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()
    REQUEST_COUNT.labels('DELETE', '/api/tasks', '200').inc()
    return jsonify({'message': 'Task deleted'})

@app.route('/health')
def health():
    """Health check endpoint — Jenkins and monitoring use this."""
    return jsonify({'status': 'healthy', 'app': 'TaskFlow'}), 200

@app.route('/metrics')
def metrics():
    """Prometheus scrapes this endpoint for metrics."""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)

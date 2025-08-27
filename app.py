#!/usr/bin/env python3
import http.server
import socketserver
import os
import sqlite3
import json
import urllib.parse

PORT = 8000
DB_NAME = 'todos.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            completed BOOLEAN DEFAULT FALSE
        )
    ''')
    conn.commit()
    conn.close()

class TodoHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        elif self.path == '/api/todos':
            self.send_todos()
            return
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        if self.path == '/api/todos':
            self.add_todo()
        elif self.path.startswith('/api/todos/'):
            todo_id = self.path.split('/')[-1]
            if todo_id == 'toggle':
                self.toggle_todo()
            elif todo_id == 'delete':
                self.delete_todo()
    
    def send_todos(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.execute('SELECT id, task, completed FROM todos ORDER BY id DESC')
        todos = [{'id': row[0], 'task': row[1], 'completed': bool(row[2])} for row in cursor.fetchall()]
        conn.close()
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(todos).encode())
    
    def add_todo(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(post_data)
        
        conn = sqlite3.connect(DB_NAME)
        conn.execute('INSERT INTO todos (task) VALUES (?)', (data['task'],))
        conn.commit()
        conn.close()
        
        self.send_response(201)
        self.end_headers()
    
    def toggle_todo(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(post_data)
        
        conn = sqlite3.connect(DB_NAME)
        conn.execute('UPDATE todos SET completed = ? WHERE id = ?', (data['completed'], data['id']))
        conn.commit()
        conn.close()
        
        self.send_response(200)
        self.end_headers()
    
    def delete_todo(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(post_data)
        
        conn = sqlite3.connect(DB_NAME)
        conn.execute('DELETE FROM todos WHERE id = ?', (data['id'],))
        conn.commit()
        conn.close()
        
        self.send_response(200)
        self.end_headers()

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    init_db()
    
    with socketserver.TCPServer(("", PORT), TodoHandler) as httpd:
        print(f"Todo app running at http://localhost:{PORT}")
        httpd.serve_forever()
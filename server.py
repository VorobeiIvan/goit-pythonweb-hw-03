from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import urllib.parse
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
FILE_PATH = BASE_DIR / "data.json"


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        route = urllib.parse.urlparse(self.path).path
        if route == "/":
            self.serve_html("index.html")
        elif route == "/read":
            self.render_messages_page()
        elif route == "/message":
            self.serve_html("message.html")
        else:
            file_path = BASE_DIR / route[1:]
            if file_path.exists():
                self.serve_static(file_path)
            else:
                self.serve_html("error.html", 404)

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length).decode("utf-8")
        parsed_data = urllib.parse.parse_qs(post_data)
        message_data = {key: value[0] for key, value in parsed_data.items()}
        self.store_message(message_data)
        self.send_response(303)
        self.send_header("Location", "/read")
        self.end_headers()

    def serve_html(self, filename, status=200):
        file_path = BASE_DIR / filename
        if file_path.exists():
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            with open(file_path, "r", encoding="utf-8") as file:
                self.wfile.write(file.read().encode("utf-8"))
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h1>404 Not Found</h1>")

    def serve_static(self, file_path):
        try:
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.end_headers()
            with open(file_path, "rb") as file:
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.serve_html("error.html", 404)

    def render_messages_page(self):
        messages = self.load_messages()
        content = "".join(f"<p>{time}: {msg}</p>" for time, msg in messages.items())
        page = f"""
        <html>
        <head><title>Messages</title></head>
        <body>
            <h1>Stored Messages</h1>
            {content}
            <br><a href="/">Go back</a>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))

    def store_message(self, data: dict):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        if not FILE_PATH.exists():
            FILE_PATH.write_text("{}", encoding="utf-8")
        try:
            with FILE_PATH.open("r", encoding="utf-8") as file:
                messages = json.load(file)
        except json.JSONDecodeError:
            messages = {}
        messages[timestamp] = data
        with FILE_PATH.open("w", encoding="utf-8") as file:
            json.dump(messages, file, ensure_ascii=False, indent=4)

    def load_messages(self):
        if not FILE_PATH.exists():
            return {}
        try:
            with FILE_PATH.open("r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return {}


def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=8000):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    print(f"Serving on port {port}...")
    httpd.serve_forever()


if __name__ == "__main__":
    run()

from datetime import datetime
import mimetypes
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from jinja2 import Template

BASE_DIR = Path(__file__).resolve().parent
FILE_PATH = BASE_DIR / "storage" / "data.json"


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        route = urllib.parse.urlparse(self.path).path
        match route:
            case "/":
                self.serve_html("index.html")
            case "/read":
                self.render_messages_page()
            case "/message":
                self.serve_html("message.html")
            case _:
                file_path = BASE_DIR / route[1:]
                if file_path.exists():
                    self.serve_static(file_path)
                else:
                    self.serve_html("error.html", 404)

    def do_POST(self) -> None:
        size = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(size).decode("utf-8")
        parsed_data = urllib.parse.parse_qs(data)
        message_data = {key: value[0] for key, value in parsed_data.items()}

        self.store_message(message_data)

        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def serve_html(self, filename: str, status_code: int = 200) -> None:
        file_path = BASE_DIR / filename
        if file_path.exists():
            self.send_response(status_code)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open(file_path, "rb") as file:
                self.wfile.write(file.read())
        else:
            self.send_error(404, "File not found")

    def serve_static(self, file_path: Path) -> None:
        self.send_response(200)
        mime_type, _ = mimetypes.guess_type(file_path)
        self.send_header("Content-type", mime_type or "application/octet-stream")
        self.end_headers()
        with open(file_path, "rb") as file:
            self.wfile.write(file.read())

    def store_message(self, data: dict) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        try:
            messages = json.loads(FILE_PATH.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            messages = {}

        messages[timestamp] = data

        FILE_PATH.write_text(json.dumps(messages, ensure_ascii=False, indent=4), encoding="utf-8")

    def render_messages_page(self) -> None:
        try:
            messages = json.loads(FILE_PATH.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            messages = {}

        template_path = BASE_DIR / "read.html"
        template = Template(template_path.read_text(encoding="utf-8"))
        rendered_html = template.render(messages=messages)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(rendered_html.encode("utf-8"))


def run_server(host="0.0.0.0", port=3000) -> None:
    server_address = (host, port)
    http = HTTPServer(server_address, RequestHandler)
    print(f"Starting server on {host}:{port}...")

    try:
        http.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        http.server_close()


if __name__ == "__main__":
    run_server()

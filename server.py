from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"MicroScalper Server Running")

    def do_POST(self):
        if self.path == "/postback":
            length = int(self.headers.get('Content-Length', 0))
            data = self.rfile.read(length)
            print("📩 POSTBACK RECEIVED:", data.decode())

            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

server = HTTPServer(("0.0.0.0", 8000), Handler)
print("✅ Server running on port 8000")
server.serve_forever()

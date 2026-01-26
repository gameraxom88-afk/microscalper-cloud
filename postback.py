from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/postback":
            length = int(self.headers['Content-Length'])
            data = self.rfile.read(length)
            payload = json.loads(data)
            print("📩 New postback received:", payload)
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

server = HTTPServer(('0.0.0.0', 8000), WebhookHandler)
print("🚀 Postback server running on port 8000")
server.serve_forever()

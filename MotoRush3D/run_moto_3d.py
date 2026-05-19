import http.server
import socketserver
import webbrowser
import os

PORT = 0
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

# Fix for Windows registry sometimes assigning incorrect MIME types
Handler.extensions_map['.js'] = 'application/javascript'
Handler.extensions_map['.css'] = 'text/css'

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    actual_port = httpd.server_address[1]
    print(f"Starting Moto Rush 3D Server at http://localhost:{actual_port}")
    print("Opening in your web browser...")
    webbrowser.open(f"http://localhost:{actual_port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")

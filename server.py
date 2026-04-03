import http.server, os, sys

port = int(os.environ.get('PORT', sys.argv[1] if len(sys.argv) > 1 else 5000))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
handler = http.server.SimpleHTTPRequestHandler
httpd = http.server.HTTPServer(('', port), handler)
print(f'Serving on port {port}')
httpd.serve_forever()

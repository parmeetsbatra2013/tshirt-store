import sqlite3, json, os, sys
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cart.db')

# ── Database setup ──────────────────────────────────────────────────────────
def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            product_id INTEGER PRIMARY KEY,
            name       TEXT    NOT NULL,
            emoji      TEXT    NOT NULL,
            price      REAL    NOT NULL,
            qty        INTEGER NOT NULL DEFAULT 1
        )
    ''')
    con.commit()
    con.close()

def db():
    return sqlite3.connect(DB_PATH)

# ── HTTP Handler ─────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):

    # ── routing ──
    def do_GET(self):
        if urlparse(self.path).path == '/api/cart':
            self._get_cart()
        else:
            self._static()

    def do_POST(self):
        p = urlparse(self.path).path
        if   p == '/api/cart/add':    self._add()
        elif p == '/api/cart/update': self._update()
        elif p == '/api/cart/clear':  self._clear()
        else: self._not_found()

    def do_DELETE(self):
        if urlparse(self.path).path == '/api/cart/remove':
            self._remove()
        else:
            self._not_found()

    def do_OPTIONS(self):           # CORS pre-flight
        self.send_response(204)
        self._cors()
        self.end_headers()

    # ── cart API ──
    def _get_cart(self):
        con = db()
        rows = con.execute(
            'SELECT product_id, name, emoji, price, qty FROM cart'
        ).fetchall()
        con.close()
        items = [{'id': r[0], 'name': r[1], 'emoji': r[2],
                  'price': r[3], 'qty': r[4]} for r in rows]
        self._json(items)

    def _add(self):
        data = self._body()
        con = db()
        existing = con.execute(
            'SELECT qty FROM cart WHERE product_id = ?', (data['id'],)
        ).fetchone()
        if existing:
            con.execute('UPDATE cart SET qty = qty + 1 WHERE product_id = ?',
                        (data['id'],))
        else:
            con.execute(
                'INSERT INTO cart (product_id, name, emoji, price, qty) VALUES (?,?,?,?,1)',
                (data['id'], data['name'], data['emoji'], data['price'])
            )
        con.commit()
        con.close()
        self._json({'ok': True})

    def _update(self):
        data = self._body()
        con = db()
        if data['qty'] <= 0:
            con.execute('DELETE FROM cart WHERE product_id = ?', (data['id'],))
        else:
            con.execute('UPDATE cart SET qty = ? WHERE product_id = ?',
                        (data['qty'], data['id']))
        con.commit()
        con.close()
        self._json({'ok': True})

    def _remove(self):
        data = self._body()
        con = db()
        con.execute('DELETE FROM cart WHERE product_id = ?', (data['id'],))
        con.commit()
        con.close()
        self._json({'ok': True})

    def _clear(self):
        con = db()
        con.execute('DELETE FROM cart')
        con.commit()
        con.close()
        self._json({'ok': True})

    # ── static file serving ──
    def _static(self):
        path = urlparse(self.path).path
        if path == '/':
            path = '/index.html'
        file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), path.lstrip('/')
        )
        if os.path.isfile(file_path):
            ext = os.path.splitext(file_path)[1]
            mime = {'.html': 'text/html', '.css': 'text/css',
                    '.js': 'application/javascript'}.get(ext, 'application/octet-stream')
            with open(file_path, 'rb') as f:
                body = f.read()
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', len(body))
            self._cors()
            self.end_headers()
            self.wfile.write(body)
        else:
            self._not_found()

    # ── helpers ──
    def _body(self):
        length = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(length))

    def _json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _not_found(self):
        self.send_response(404)
        self.end_headers()

    def log_message(self, fmt, *args):
        print(f'[{self.log_date_time_string()}] {fmt % args}')

# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', sys.argv[1] if len(sys.argv) > 1 else 5000))
    print(f'Batra Store running at http://localhost:{port}')
    print(f'SQLite DB: {DB_PATH}')
    ThreadingHTTPServer(('', port), Handler).serve_forever()

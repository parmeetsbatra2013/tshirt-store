import sqlite3, json, os, sys, uuid
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from http.cookies import SimpleCookie

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cart.db')

# ── Database setup ──────────────────────────────────────────────────────────
def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT    NOT NULL,
            emoji    TEXT    NOT NULL,
            price    REAL    NOT NULL,
            category TEXT    NOT NULL,
            badge    TEXT,
            stock    INTEGER NOT NULL DEFAULT 100
        )
    ''')
    con.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT    NOT NULL,
            product_id INTEGER NOT NULL,
            name       TEXT    NOT NULL,
            emoji      TEXT    NOT NULL,
            price      REAL    NOT NULL,
            qty        INTEGER NOT NULL DEFAULT 1,
            UNIQUE(session_id, product_id)
        )
    ''')
    con.commit()
    con.close()

def db():
    con = sqlite3.connect(DB_PATH)
    con.execute('PRAGMA journal_mode=WAL')
    return con

# ── HTTP Handler ─────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):

    # ── session ──
    def _get_session(self):
        raw = self.headers.get('Cookie', '')
        cookie = SimpleCookie(raw)
        if 'session_id' in cookie:
            return cookie['session_id'].value
        return None

    def _new_session(self):
        return str(uuid.uuid4())

    # ── routing ──
    def do_GET(self):
        p = urlparse(self.path).path
        if   p == '/api/cart':     self._get_cart()
        elif p == '/api/products': self._get_products()
        else:                      self._static()

    def do_POST(self):
        p = urlparse(self.path).path
        if   p == '/api/cart/add':      self._add()
        elif p == '/api/cart/update':   self._update()
        elif p == '/api/cart/clear':    self._clear()
        elif p == '/api/products':      self._create_product()
        elif p.startswith('/api/products/'): self._update_product(p)
        else: self._not_found()

    def do_DELETE(self):
        p = urlparse(self.path).path
        if   p == '/api/cart/remove':        self._remove()
        elif p.startswith('/api/products/'): self._delete_product(p)
        else:                                self._not_found()

    def do_OPTIONS(self):           # CORS pre-flight
        self.send_response(204)
        self._cors()
        self.end_headers()

    # ── products API ──
    def _get_products(self):
        con = db()
        rows = con.execute(
            'SELECT id, name, emoji, price, category, badge, stock FROM products ORDER BY id'
        ).fetchall()
        con.close()
        self._json([{'id': r[0], 'name': r[1], 'emoji': r[2], 'price': r[3],
                     'category': r[4], 'badge': r[5], 'stock': r[6]} for r in rows])

    def _create_product(self):
        data = self._body()
        con = db()
        cur = con.execute(
            'INSERT INTO products (name, emoji, price, category, badge, stock) VALUES (?,?,?,?,?,?)',
            (data['name'], data['emoji'], float(data['price']),
             data['category'], data.get('badge') or None, int(data.get('stock', 100)))
        )
        con.commit()
        pid = cur.lastrowid
        con.close()
        self._json({'ok': True, 'id': pid})

    def _update_product(self, path):
        pid = path.split('/')[-1]
        data = self._body()
        con = db()
        con.execute(
            'UPDATE products SET name=?, emoji=?, price=?, category=?, badge=?, stock=? WHERE id=?',
            (data['name'], data['emoji'], float(data['price']),
             data['category'], data.get('badge') or None, int(data.get('stock', 100)), pid)
        )
        con.commit()
        con.close()
        self._json({'ok': True})

    def _delete_product(self, path):
        pid = path.split('/')[-1]
        con = db()
        con.execute('DELETE FROM products WHERE id = ?', (pid,))
        con.commit()
        con.close()
        self._json({'ok': True})

    # ── cart API ──
    def _get_cart(self):
        sid = self._get_session()
        new_session = sid is None
        if new_session:
            sid = self._new_session()
        con = db()
        rows = con.execute(
            'SELECT product_id, name, emoji, price, qty FROM cart WHERE session_id = ?',
            (sid,)
        ).fetchall()
        con.close()
        items = [{'id': r[0], 'name': r[1], 'emoji': r[2],
                  'price': r[3], 'qty': r[4]} for r in rows]
        self._json(items, set_session=sid if new_session else None)

    def _add(self):
        sid = self._get_session()
        new_session = sid is None
        if new_session:
            sid = self._new_session()
        data = self._body()
        con = db()
        existing = con.execute(
            'SELECT qty FROM cart WHERE session_id = ? AND product_id = ?',
            (sid, data['id'])
        ).fetchone()
        if existing:
            con.execute(
                'UPDATE cart SET qty = qty + 1 WHERE session_id = ? AND product_id = ?',
                (sid, data['id'])
            )
        else:
            con.execute(
                'INSERT INTO cart (session_id, product_id, name, emoji, price, qty) VALUES (?,?,?,?,?,1)',
                (sid, data['id'], data['name'], data['emoji'], data['price'])
            )
        con.commit()
        con.close()
        self._json({'ok': True}, set_session=sid if new_session else None)

    def _update(self):
        sid = self._get_session()
        if not sid:
            self._json({'ok': False}, status=400)
            return
        data = self._body()
        con = db()
        if data['qty'] <= 0:
            con.execute(
                'DELETE FROM cart WHERE session_id = ? AND product_id = ?',
                (sid, data['id'])
            )
        else:
            con.execute(
                'UPDATE cart SET qty = ? WHERE session_id = ? AND product_id = ?',
                (data['qty'], sid, data['id'])
            )
        con.commit()
        con.close()
        self._json({'ok': True})

    def _remove(self):
        sid = self._get_session()
        if not sid:
            self._json({'ok': False}, status=400)
            return
        data = self._body()
        con = db()
        con.execute(
            'DELETE FROM cart WHERE session_id = ? AND product_id = ?',
            (sid, data['id'])
        )
        con.commit()
        con.close()
        self._json({'ok': True})

    def _clear(self):
        sid = self._get_session()
        if not sid:
            self._json({'ok': True})
            return
        con = db()
        con.execute('DELETE FROM cart WHERE session_id = ?', (sid,))
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

    def _json(self, data, status=200, set_session=None):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        if set_session:
            self.send_header(
                'Set-Cookie',
                f'session_id={set_session}; Path=/; HttpOnly; SameSite=Lax'
            )
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

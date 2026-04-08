// ─── CART STATE (SQLite-backed via REST API) ──────────────────────────────
let cart = [];   // local cache, always synced from server

// Use same origin so it works on any port (8080 local, or deployed)
const API = window.location.origin;

// ── Load cart from SQLite (with retry) ──
async function loadCart() {
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      const res = await fetch(API + '/api/cart');
      if (res.ok) {
        cart = await res.json();
        updateCartUI();
        return;
      }
    } catch {
      if (attempt < 3) await new Promise(r => setTimeout(r, 300 * attempt));
    }
  }
  cart = [];
  updateCartUI();
}

// ── Add item ──
async function addToCart(id, e) {
  if (e) e.stopPropagation();
  const product = PRODUCTS.find(p => p.id === id);
  await fetch(API + '/api/cart/add', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({
      id:    product.id,
      name:  product.name,
      emoji: product.emoji,
      price: product.price
    })
  });
  await loadCart();
  showToast(product.emoji + ' ' + product.name + ' added to cart!');
}

// ── Remove item ──
async function removeFromCart(id) {
  await fetch(API + '/api/cart/remove', {
    method:  'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ id })
  });
  await loadCart();
}

// ── Change quantity (+/-) ──
async function changeQty(id, delta) {
  const item = cart.find(i => i.id === id);
  if (!item) return;
  await fetch(API + '/api/cart/update', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ id, qty: item.qty + delta })
  });
  await loadCart();
}

// ── Render cart UI ──
function updateCartUI() {
  const total = cart.reduce((s, i) => s + i.price * i.qty, 0);
  const count = cart.reduce((s, i) => s + i.qty, 0);

  document.getElementById('cartCount').textContent = count;

  const footer  = document.getElementById('cartFooter');
  const itemsEl = document.getElementById('cartItems');

  if (cart.length === 0) {
    itemsEl.innerHTML = '<p class="cart-empty">Your cart is empty</p>';
    footer.style.display = 'none';
    return;
  }

  itemsEl.innerHTML = cart.map(i => `
    <div class="cart-item">
      <div class="cart-item-img">${i.emoji}</div>
      <div class="cart-item-info">
        <h4>${i.name}</h4>
        <p>$${i.price.toFixed(2)} each</p>
      </div>
      <div class="qty-ctrl">
        <button class="qty-btn" onclick="changeQty(${i.id}, -1)">-</button>
        <span>${i.qty}</span>
        <button class="qty-btn" onclick="changeQty(${i.id}, 1)">+</button>
      </div>
      <button class="remove-item" onclick="removeFromCart(${i.id})">X</button>
    </div>
  `).join('');

  document.getElementById('cartTotal').textContent = '$' + total.toFixed(2);
  footer.style.display = 'block';
}

// ── Panel open / close ──
function openCart() {
  document.getElementById('cartPanel').classList.add('open');
  document.getElementById('overlay').classList.add('open');
}

function closeCart() {
  document.getElementById('cartPanel').classList.remove('open');
  document.getElementById('overlay').classList.remove('open');
}

// ─── INIT ───
loadCart();   // load cart from SQLite on page start

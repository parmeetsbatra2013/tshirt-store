// ─── CART STATE & FUNCTIONS ───
let cart = [];

function addToCart(id, e) {
  e.stopPropagation();
  const product = PRODUCTS.find(p => p.id === id);
  const existing = cart.find(i => i.id === id);
  if (existing) {
    existing.qty++;
  } else {
    cart.push({ ...product, qty: 1 });
  }
  updateCartUI();
  showToast(`${product.emoji} ${product.name} added to cart!`);
}

function removeFromCart(id) {
  cart = cart.filter(i => i.id !== id);
  updateCartUI();
}

function changeQty(id, delta) {
  const item = cart.find(i => i.id === id);
  if (!item) return;
  item.qty += delta;
  if (item.qty <= 0) removeFromCart(id);
  else updateCartUI();
}

function updateCartUI() {
  const total = cart.reduce((s, i) => s + i.price * i.qty, 0);
  const count = cart.reduce((s, i) => s + i.qty, 0);
  document.getElementById('cartCount').textContent = count;
  const footer = document.getElementById('cartFooter');
  const itemsEl = document.getElementById('cartItems');

  if (cart.length === 0) {
    itemsEl.innerHTML = '<p class="cart-empty">Your cart is empty 🛒</p>';
    footer.style.display = 'none';
  } else {
    itemsEl.innerHTML = cart.map(i => `
      <div class="cart-item">
        <div class="cart-item-img">${i.emoji}</div>
        <div class="cart-item-info">
          <h4>${i.name}</h4>
          <p>$${i.price.toFixed(2)} each</p>
        </div>
        <div class="qty-ctrl">
          <button class="qty-btn" onclick="changeQty(${i.id}, -1)">−</button>
          <span>${i.qty}</span>
          <button class="qty-btn" onclick="changeQty(${i.id}, 1)">+</button>
        </div>
        <button class="remove-item" onclick="removeFromCart(${i.id})">🗑</button>
      </div>
    `).join('');
    document.getElementById('cartTotal').textContent = `$${total.toFixed(2)}`;
    footer.style.display = 'block';
  }
}

function openCart() {
  document.getElementById('cartPanel').classList.add('open');
  document.getElementById('overlay').classList.add('open');
}

function closeCart() {
  document.getElementById('cartPanel').classList.remove('open');
  document.getElementById('overlay').classList.remove('open');
}

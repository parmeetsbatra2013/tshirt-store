// ─── APP STATE & UI ───
let currentFilter = 'all';

function renderProducts(filter = 'all') {
  const grid = document.getElementById('productGrid');
  const filtered = filter === 'all' ? PRODUCTS : PRODUCTS.filter(p => p.category === filter);
  grid.innerHTML = filtered.map(p => `
    <div class="card" data-id="${p.id}">
      <div class="card-img">${p.emoji}</div>
      <div class="card-body">
        <h3>${p.name}${p.badge ? `<span class="badge">${p.badge}</span>` : ''}</h3>
        <p class="category">${p.category.charAt(0).toUpperCase() + p.category.slice(1)}</p>
      </div>
      <div class="card-footer">
        <span class="price">$${p.price.toFixed(2)}</span>
        <button class="add-btn" onclick="addToCart(${p.id}, event)">Add to Cart</button>
      </div>
    </div>
  `).join('');
}

function filterProducts(filter, btn) {
  currentFilter = filter;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderProducts(filter);
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}

function submitContact() {
  const name = document.getElementById('contactName').value.trim();
  const email = document.getElementById('contactEmail').value.trim();
  const msg = document.getElementById('contactMessage').value.trim();
  if (!name || !email || !msg) { showToast('Please fill in all fields.'); return; }
  document.getElementById('contactName').value = '';
  document.getElementById('contactEmail').value = '';
  document.getElementById('contactMessage').value = '';
  showToast('✅ Message sent! We\'ll get back to you soon.');
}

// ─── INIT ───
renderProducts();
updateCartUI();

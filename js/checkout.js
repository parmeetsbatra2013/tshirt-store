// ─── CHECKOUT FUNCTIONS ───
function openCheckout() {
  closeCart();
  const subtotal = cart.reduce((s, i) => s + i.price * i.qty, 0);
  const shipping = subtotal >= 50 ? 0 : 5.99;
  const tax = subtotal * 0.08;
  const total = subtotal + shipping + tax;
  document.getElementById('orderSummary').innerHTML = `
    <h3>Order Summary</h3>
    ${cart.map(i => `<div class="summary-line"><span>${i.emoji} ${i.name} × ${i.qty}</span><span>$${(i.price * i.qty).toFixed(2)}</span></div>`).join('')}
    <div class="summary-line"><span>Subtotal</span><span>$${subtotal.toFixed(2)}</span></div>
    <div class="summary-line"><span>Shipping</span><span>${shipping === 0 ? '🎉 Free' : `$${shipping.toFixed(2)}`}</span></div>
    <div class="summary-line"><span>Tax (8%)</span><span>$${tax.toFixed(2)}</span></div>
    <div class="summary-line total"><span>Total</span><span>$${total.toFixed(2)}</span></div>
  `;
  document.getElementById('checkoutModal').classList.add('open');
}

function closeCheckout() {
  document.getElementById('checkoutModal').classList.remove('open');
}

function placeOrder() {
  const fields = ['firstName', 'lastName', 'email', 'address', 'city', 'zip', 'cardNum', 'expiry', 'cvv'];
  for (const f of fields) {
    if (!document.getElementById(f).value.trim()) {
      showToast('Please fill in all fields.');
      document.getElementById(f).focus();
      return;
    }
  }
  document.getElementById('modalContent').innerHTML = `
    <div class="success-screen">
      <div class="success-icon">🎉</div>
      <h2>Order Placed!</h2>
      <p>Thanks for shopping with Batra! Your t-shirts are on their way.</p>
      <p style="font-size:.85rem;color:#aaa;">Order confirmation will be sent to your email.</p>
      <button class="place-order-btn" style="margin-top:1.5rem" onclick="finishOrder()">Continue Shopping</button>
    </div>
  `;
}

function finishOrder() {
  cart = [];
  updateCartUI();
  closeCheckout();
}

// ─── INPUT FORMATTERS ───
function formatCard(el) {
  let v = el.value.replace(/\D/g, '').substring(0, 16);
  el.value = v.replace(/(.{4})/g, '$1 ').trim();
}

function formatExpiry(el) {
  let v = el.value.replace(/\D/g, '').substring(0, 4);
  if (v.length >= 2) v = v.substring(0, 2) + '/' + v.substring(2);
  el.value = v;
}

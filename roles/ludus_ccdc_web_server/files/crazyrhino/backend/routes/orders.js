const express = require('express');
const { getDb } = require('../database');
const { authenticateToken } = require('../middleware/auth');

const router = express.Router();

router.use(authenticateToken);

function generateOrderNumber() {
  const ts = Date.now().toString(36).toUpperCase();
  const rand = Math.random().toString(36).substring(2, 6).toUpperCase();
  return `WKZ-${ts}-${rand}`;
}

router.post('/checkout', (req, res) => {
  const { shipping_name, shipping_email, shipping_address, shipping_city, shipping_state, shipping_zip, payment_last4 = '4242' } = req.body;

  if (!shipping_name || !shipping_email || !shipping_address || !shipping_city || !shipping_state || !shipping_zip) {
    return res.status(400).json({ error: 'All shipping fields are required' });
  }

  const db = getDb();
  const cartItems = db.prepare(`
    SELECT ci.quantity, p.id as product_id, p.name, p.price, p.stock
    FROM cart_items ci
    JOIN products p ON ci.product_id = p.id
    WHERE ci.user_id = ? AND p.active = 1
  `).all(req.user.id);

  if (cartItems.length === 0) {
    return res.status(400).json({ error: 'Cart is empty' });
  }

  const subtotal = cartItems.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const tax = parseFloat((subtotal * 0.08).toFixed(2));
  const total = parseFloat((subtotal + tax).toFixed(2));
  const orderNumber = generateOrderNumber();

  const placeOrder = db.transaction(() => {
    const orderResult = db.prepare(`
      INSERT INTO orders (user_id, order_number, subtotal, tax, total, shipping_name, shipping_email, shipping_address, shipping_city, shipping_state, shipping_zip, payment_last4)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(req.user.id, orderNumber, subtotal, tax, total, shipping_name, shipping_email, shipping_address, shipping_city, shipping_state, shipping_zip, payment_last4);

    const orderId = orderResult.lastInsertRowid;

    const insertItem = db.prepare('INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price) VALUES (?, ?, ?, ?, ?)');
    for (const item of cartItems) {
      insertItem.run(orderId, item.product_id, item.name, item.quantity, item.price);
    }

    db.prepare('DELETE FROM cart_items WHERE user_id = ?').run(req.user.id);

    return orderId;
  });

  try {
    const orderId = placeOrder();
    const order = db.prepare('SELECT * FROM orders WHERE id = ?').get(orderId);
    const items = db.prepare('SELECT * FROM order_items WHERE order_id = ?').all(orderId);
    res.status(201).json({ ...order, items });
  } catch (err) {
    res.status(500).json({ error: 'Order placement failed' });
  }
});

router.get('/', (req, res) => {
  const db = getDb();
  const orders = db.prepare('SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC').all(req.user.id);
  const result = orders.map(order => {
    const items = db.prepare('SELECT * FROM order_items WHERE order_id = ?').all(order.id);
    return { ...order, items };
  });
  res.json(result);
});

router.get('/:orderNumber', (req, res) => {
  const db = getDb();
  // VULN: IDOR — order_number lookup does not verify user_id ownership
  // Any authenticated user can view any order by guessing the order number
  // Secure option (DISABLED): AND user_id = ? in the WHERE clause
  const order = db.prepare('SELECT * FROM orders WHERE order_number = ?').get(req.params.orderNumber);
  if (!order) return res.status(404).json({ error: 'Order not found' });
  const items = db.prepare('SELECT * FROM order_items WHERE order_id = ?').all(order.id);
  res.json({ ...order, items });
});

module.exports = router;

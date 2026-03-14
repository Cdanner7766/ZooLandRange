const express = require('express');
const { getDb } = require('../database');
const { authenticateToken, requireAdmin } = require('../middleware/auth');

const router = express.Router();

router.use(authenticateToken, requireAdmin);

// Dashboard stats
router.get('/stats', (req, res) => {
  const db = getDb();
  const totalOrders = db.prepare('SELECT COUNT(*) as count FROM orders').get();
  const totalRevenue = db.prepare('SELECT COALESCE(SUM(total), 0) as total FROM orders').get();
  const totalUsers = db.prepare("SELECT COUNT(*) as count FROM users WHERE role = 'customer'").get();
  const totalProducts = db.prepare('SELECT COUNT(*) as count FROM products WHERE active = 1').get();
  const recentOrders = db.prepare('SELECT o.*, u.username FROM orders o JOIN users u ON o.user_id = u.id ORDER BY o.created_at DESC LIMIT 10').all();

  res.json({
    totalOrders: totalOrders.count,
    totalRevenue: totalRevenue.total,
    totalUsers: totalUsers.count,
    totalProducts: totalProducts.count,
    recentOrders,
  });
});

// Products CRUD
router.get('/products', (req, res) => {
  const db = getDb();
  const products = db.prepare('SELECT * FROM products ORDER BY category, name').all();
  res.json(products);
});

router.post('/products', (req, res) => {
  const { name, description, price, category, image_url, stock } = req.body;
  if (!name || !price || !category) {
    return res.status(400).json({ error: 'Name, price, and category are required' });
  }
  const db = getDb();
  const result = db.prepare('INSERT INTO products (name, description, price, category, image_url, stock) VALUES (?, ?, ?, ?, ?, ?)').run(name, description || '', price, category, image_url || '', stock || 100);
  res.status(201).json({ id: result.lastInsertRowid, name, description, price, category, image_url, stock });
});

router.put('/products/:id', (req, res) => {
  const { name, description, price, category, image_url, stock, active } = req.body;
  const db = getDb();
  const existing = db.prepare('SELECT * FROM products WHERE id = ?').get(req.params.id);
  if (!existing) return res.status(404).json({ error: 'Product not found' });

  db.prepare('UPDATE products SET name = ?, description = ?, price = ?, category = ?, image_url = ?, stock = ?, active = ? WHERE id = ?').run(
    name ?? existing.name,
    description ?? existing.description,
    price ?? existing.price,
    category ?? existing.category,
    image_url ?? existing.image_url,
    stock ?? existing.stock,
    active ?? existing.active,
    req.params.id
  );
  res.json({ message: 'Product updated' });
});

router.delete('/products/:id', (req, res) => {
  const db = getDb();
  db.prepare('UPDATE products SET active = 0 WHERE id = ?').run(req.params.id);
  res.json({ message: 'Product deactivated' });
});

// Orders management
router.get('/orders', (req, res) => {
  const db = getDb();
  const orders = db.prepare('SELECT o.*, u.username FROM orders o JOIN users u ON o.user_id = u.id ORDER BY o.created_at DESC').all();
  const result = orders.map(order => {
    const items = db.prepare('SELECT * FROM order_items WHERE order_id = ?').all(order.id);
    return { ...order, items };
  });
  res.json(result);
});

router.put('/orders/:id/status', (req, res) => {
  const { status } = req.body;
  const validStatuses = ['confirmed', 'processing', 'shipped', 'delivered', 'cancelled'];
  if (!validStatuses.includes(status)) {
    return res.status(400).json({ error: 'Invalid status' });
  }
  const db = getDb();
  const result = db.prepare('UPDATE orders SET status = ? WHERE id = ?').run(status, req.params.id);
  if (result.changes === 0) return res.status(404).json({ error: 'Order not found' });
  res.json({ message: 'Order status updated' });
});

// Users management
router.get('/users', (req, res) => {
  const db = getDb();
  const users = db.prepare('SELECT id, username, email, role, created_at FROM users ORDER BY created_at DESC').all();
  res.json(users);
});

module.exports = router;

const express = require('express');
const { getDb } = require('../database');
const { authenticateToken } = require('../middleware/auth');

const router = express.Router();

router.use(authenticateToken);

router.get('/', (req, res) => {
  const db = getDb();
  const items = db.prepare(`
    SELECT ci.id, ci.quantity, ci.added_at,
           p.id as product_id, p.name, p.description, p.price, p.category, p.image_url, p.stock
    FROM cart_items ci
    JOIN products p ON ci.product_id = p.id
    WHERE ci.user_id = ? AND p.active = 1
    ORDER BY ci.added_at
  `).all(req.user.id);
  res.json(items);
});

router.post('/add', (req, res) => {
  const { product_id, quantity = 1 } = req.body;

  if (!product_id || quantity < 1) {
    return res.status(400).json({ error: 'Valid product_id and quantity required' });
  }

  const db = getDb();
  const product = db.prepare('SELECT * FROM products WHERE id = ? AND active = 1').get(product_id);
  if (!product) return res.status(404).json({ error: 'Product not found' });

  try {
    db.prepare(`
      INSERT INTO cart_items (user_id, product_id, quantity)
      VALUES (?, ?, ?)
      ON CONFLICT(user_id, product_id) DO UPDATE SET quantity = quantity + excluded.quantity
    `).run(req.user.id, product_id, quantity);

    res.json({ message: 'Added to cart' });
  } catch (err) {
    res.status(500).json({ error: 'Failed to add to cart' });
  }
});

router.put('/:itemId', (req, res) => {
  const { quantity } = req.body;
  const db = getDb();

  if (quantity < 1) {
    db.prepare('DELETE FROM cart_items WHERE id = ? AND user_id = ?').run(req.params.itemId, req.user.id);
    return res.json({ message: 'Item removed' });
  }

  const result = db.prepare('UPDATE cart_items SET quantity = ? WHERE id = ? AND user_id = ?').run(quantity, req.params.itemId, req.user.id);
  if (result.changes === 0) return res.status(404).json({ error: 'Cart item not found' });
  res.json({ message: 'Cart updated' });
});

router.delete('/:itemId', (req, res) => {
  const db = getDb();
  const result = db.prepare('DELETE FROM cart_items WHERE id = ? AND user_id = ?').run(req.params.itemId, req.user.id);
  if (result.changes === 0) return res.status(404).json({ error: 'Cart item not found' });
  res.json({ message: 'Item removed' });
});

router.delete('/', (req, res) => {
  const db = getDb();
  db.prepare('DELETE FROM cart_items WHERE user_id = ?').run(req.user.id);
  res.json({ message: 'Cart cleared' });
});

module.exports = router;

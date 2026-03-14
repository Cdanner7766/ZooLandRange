const express = require('express');
const { getDb } = require('../database');

const router = express.Router();

router.get('/', (req, res) => {
  const { category, search } = req.query;
  const db = getDb();

  let query = 'SELECT * FROM products WHERE active = 1';
  const params = [];

  if (category && category !== 'all') {
    query += ' AND category = ?';
    params.push(category);
  }
  if (search) {
    // VULN: SQL injection — search parameter concatenated directly into query
    // Secure option (DISABLED): use parameterized ? placeholders
    query += ` AND (name LIKE '%${search}%' OR description LIKE '%${search}%')`;
  }

  query += ' ORDER BY category, name';

  const products = db.prepare(query).all(...params);
  res.json(products);
});

router.get('/:id', (req, res) => {
  const db = getDb();
  const product = db.prepare('SELECT * FROM products WHERE id = ? AND active = 1').get(req.params.id);
  if (!product) return res.status(404).json({ error: 'Product not found' });
  res.json(product);
});

module.exports = router;

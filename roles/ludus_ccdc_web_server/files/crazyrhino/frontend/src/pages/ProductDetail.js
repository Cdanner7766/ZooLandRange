import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../api';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import './ProductDetail.css';

const EMOJIS = {
  lion: '🦁', elephant: '🐘', penguin: '🐧', giraffe: '🦒', tiger: '🐯', panda: '🐼',
  ticket: '🎟️', admission: '🎟️', membership: '⭐', tour: '🦜', safari: '🦜',
  encounter: '🌟', feeding: '🌟', experience: '🌟', night: '🌙',
  't-shirt': '👕', tee: '👕', hoodie: '🧥', hat: '🧢', cap: '🧢',
  bag: '🎒', backpack: '🎒', tote: '🎒', bottle: '🫙', book: '📚',
  keychain: '🔑', globe: '🌍',
};

function getEmoji(name) {
  const lower = name.toLowerCase();
  for (const [key, emoji] of Object.entries(EMOJIS)) {
    if (lower.includes(key)) return emoji;
  }
  return '🛍️';
}

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { addToCart } = useCart();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [qty, setQty] = useState(1);
  const [adding, setAdding] = useState(false);
  const [added, setAdded] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get(`/products/${id}`).then(res => {
      setProduct(res.data);
    }).catch(() => navigate('/shop')).finally(() => setLoading(false));
  }, [id, navigate]);

  const handleAdd = async () => {
    if (!user) { navigate('/login'); return; }
    setAdding(true);
    setError('');
    try {
      await addToCart(product.id, qty);
      setAdded(true);
      setTimeout(() => setAdded(false), 3000);
    } catch {
      setError('Failed to add to cart. Please try again.');
    } finally {
      setAdding(false);
    }
  };

  if (loading) return <div className="loading">Loading product...</div>;
  if (!product) return null;

  const emoji = getEmoji(product.name);
  const isTicket = product.category === 'tickets';

  return (
    <div className="detail-page container">
      <nav className="breadcrumb">
        <Link to="/">Home</Link> › <Link to="/shop">Shop</Link> › <Link to={`/shop/${product.category}`}>{isTicket ? 'Tickets' : 'Merchandise'}</Link> › {product.name}
      </nav>

      <div className="detail-layout">
        <div className="detail-image-box">
          <span className="detail-emoji">{emoji}</span>
          <div className={`category-badge ${product.category}`}>
            {isTicket ? '🎟️ Tickets & Experiences' : '👕 Merchandise'}
          </div>
        </div>

        <div className="detail-info">
          <h1>{product.name}</h1>
          <div className="detail-price">${product.price.toFixed(2)}</div>
          <p className="detail-desc">{product.description}</p>

          {isTicket && (
            <div className="ticket-info">
              <div className="ticket-feature">✅ Digital delivery to your email</div>
              <div className="ticket-feature">✅ Valid for 1 year from purchase</div>
              <div className="ticket-feature">✅ Non-refundable · Transferable</div>
            </div>
          )}

          {!isTicket && (
            <div className="ticket-info">
              <div className="ticket-feature">📦 Free shipping on orders over $50</div>
              <div className="ticket-feature">✅ 30-day return policy</div>
              <div className="ticket-feature">🌿 Sustainably sourced materials</div>
            </div>
          )}

          {error && <div className="alert alert-error">{error}</div>}
          {added && <div className="alert alert-success">Added to cart! <Link to="/cart">View Cart →</Link></div>}

          <div className="detail-actions">
            {!isTicket && (
              <div className="qty-selector">
                <label className="form-label">Quantity</label>
                <div className="qty-controls">
                  <button onClick={() => setQty(q => Math.max(1, q - 1))}>−</button>
                  <span>{qty}</span>
                  <button onClick={() => setQty(q => q + 1)}>+</button>
                </div>
              </div>
            )}
            <div className="add-btns">
              <button
                onClick={handleAdd}
                disabled={adding}
                className="btn btn-primary btn-lg full-width"
              >
                {adding ? 'Adding...' : added ? '✓ Added to Cart!' : `Add to Cart — $${(product.price * qty).toFixed(2)}`}
              </button>
              {user && (
                <Link to="/cart" className="btn btn-outline btn-lg full-width">View Cart</Link>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

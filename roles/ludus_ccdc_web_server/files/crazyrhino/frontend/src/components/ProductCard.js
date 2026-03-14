import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import './ProductCard.css';

const ANIMAL_EMOJIS = {
  merchandise: ['👕', '🧸', '🎩', '🎒', '🖼️', '🦁', '🐘', '🦒'],
  tickets: ['🎟️', '🌟', '🦜', '🔭', '🎪'],
};

function getProductEmoji(product) {
  const name = product.name.toLowerCase();
  if (name.includes('lion')) return '🦁';
  if (name.includes('elephant')) return '🐘';
  if (name.includes('penguin')) return '🐧';
  if (name.includes('giraffe')) return '🦒';
  if (name.includes('tiger')) return '🐯';
  if (name.includes('panda')) return '🐼';
  if (name.includes('ticket') || name.includes('admission') || name.includes('pass')) return '🎟️';
  if (name.includes('membership')) return '⭐';
  if (name.includes('tour') || name.includes('safari')) return '🦜';
  if (name.includes('encounter') || name.includes('feeding') || name.includes('experience')) return '🌟';
  if (name.includes('night')) return '🌙';
  if (name.includes('t-shirt') || name.includes('tee')) return '👕';
  if (name.includes('hoodie')) return '🧥';
  if (name.includes('hat') || name.includes('cap')) return '🧢';
  if (name.includes('bag') || name.includes('backpack') || name.includes('tote')) return '🎒';
  if (name.includes('bottle')) return '🫙';
  if (name.includes('book')) return '📚';
  if (name.includes('keychain')) return '🔑';
  if (name.includes('globe')) return '🌍';
  return product.category === 'tickets' ? '🎟️' : '🛍️';
}

export default function ProductCard({ product, compact = false }) {
  const { user } = useAuth();
  const { addToCart } = useCart();
  const [adding, setAdding] = useState(false);
  const [added, setAdded] = useState(false);

  const handleAddToCart = async (e) => {
    e.preventDefault();
    if (!user) {
      window.location.href = '/login';
      return;
    }
    setAdding(true);
    try {
      await addToCart(product.id);
      setAdded(true);
      setTimeout(() => setAdded(false), 2000);
    } catch (err) {
      console.error(err);
    } finally {
      setAdding(false);
    }
  };

  const emoji = getProductEmoji(product);
  const categoryLabel = product.category === 'tickets' ? 'Tickets & Experiences' : 'Merchandise';

  return (
    <Link to={`/product/${product.id}`} className={`product-card ${compact ? 'compact' : ''}`}>
      <div className="product-image">
        <span className="product-emoji">{emoji}</span>
        <span className={`category-pill ${product.category}`}>{categoryLabel}</span>
      </div>
      <div className="product-body">
        <h3 className="product-name">{product.name}</h3>
        {!compact && <p className="product-desc">{product.description}</p>}
        <div className="product-footer">
          <span className="product-price">${product.price.toFixed(2)}</span>
          <button
            onClick={handleAddToCart}
            disabled={adding}
            className={`btn btn-sm ${added ? 'btn-primary' : 'btn-amber'}`}
          >
            {added ? '✓ Added!' : adding ? '...' : '+ Cart'}
          </button>
        </div>
      </div>
    </Link>
  );
}

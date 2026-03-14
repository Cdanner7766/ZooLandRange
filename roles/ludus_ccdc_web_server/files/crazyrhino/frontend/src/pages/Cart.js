import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import './Cart.css';

export default function Cart() {
  const { cartItems, subtotal, updateQuantity, removeItem } = useCart();
  const navigate = useNavigate();
  const tax = subtotal * 0.08;
  const total = subtotal + tax;

  if (cartItems.length === 0) {
    return (
      <div className="cart-page container">
        <div className="page-header" style={{ margin: '0 -1.5rem 2rem', padding: '2rem 1.5rem' }}>
          <h1>Your Cart</h1>
        </div>
        <div className="empty-state">
          <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🛒</div>
          <h3>Your cart is empty</h3>
          <p>Add some products to get started!</p>
          <Link to="/shop" className="btn btn-primary" style={{ marginTop: '1.5rem' }}>Shop Now</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="cart-page">
      <div className="page-header">
        <div className="container">
          <h1>🛒 Your Cart</h1>
          <p>{cartItems.length} item{cartItems.length !== 1 ? 's' : ''}</p>
        </div>
      </div>

      <div className="container cart-layout">
        <div className="cart-items">
          {cartItems.map(item => (
            <div key={item.id} className="cart-item card">
              <div className="cart-item-img">
                <span>{getCategoryEmoji(item.category)}</span>
              </div>
              <div className="cart-item-info">
                <Link to={`/product/${item.product_id}`} className="cart-item-name">{item.name}</Link>
                <div className="cart-item-price">${item.price.toFixed(2)} each</div>
                {item.category === 'tickets' ? (
                  <div className="qty-display">Qty: {item.quantity}</div>
                ) : (
                  <div className="qty-controls">
                    <button onClick={() => updateQuantity(item.id, item.quantity - 1)}>−</button>
                    <span>{item.quantity}</span>
                    <button onClick={() => updateQuantity(item.id, item.quantity + 1)}>+</button>
                  </div>
                )}
              </div>
              <div className="cart-item-total">
                <div className="item-total">${(item.price * item.quantity).toFixed(2)}</div>
                <button onClick={() => removeItem(item.id)} className="remove-btn">Remove</button>
              </div>
            </div>
          ))}
        </div>

        <div className="cart-summary card">
          <h2>Order Summary</h2>
          <div className="summary-line">
            <span>Subtotal</span>
            <span>${subtotal.toFixed(2)}</span>
          </div>
          <div className="summary-line">
            <span>Estimated Tax (8%)</span>
            <span>${tax.toFixed(2)}</span>
          </div>
          <div className="summary-line">
            <span>Shipping</span>
            <span>{subtotal >= 50 ? <span className="free-shipping">FREE</span> : '$5.99'}</span>
          </div>
          <div className="summary-divider" />
          <div className="summary-total">
            <span>Total</span>
            <span>${total.toFixed(2)}</span>
          </div>
          {subtotal < 50 && (
            <p className="shipping-note">Add ${(50 - subtotal).toFixed(2)} more for free shipping!</p>
          )}
          <button
            onClick={() => navigate('/checkout')}
            className="btn btn-primary btn-lg"
            style={{ width: '100%', marginTop: '1rem' }}
          >
            Proceed to Checkout
          </button>
          <Link to="/shop" className="btn btn-outline" style={{ width: '100%', marginTop: '0.75rem' }}>
            Continue Shopping
          </Link>
        </div>
      </div>
    </div>
  );
}

function getCategoryEmoji(category) {
  return category === 'tickets' ? '🎟️' : '🛍️';
}

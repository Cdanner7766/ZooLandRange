import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import api from '../api';
import './Checkout.css';

export default function Checkout() {
  const { user } = useAuth();
  const { cartItems, subtotal } = useCart();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const tax = subtotal * 0.08;
  const shipping = subtotal >= 50 ? 0 : 5.99;
  const total = subtotal + tax + shipping;

  const [form, setForm] = useState({
    shipping_name: user?.username || '',
    shipping_email: user?.email || '',
    shipping_address: '',
    shipping_city: '',
    shipping_state: '',
    shipping_zip: '',
    card_name: '',
    card_number: '4111 1111 1111 1111',
    card_expiry: '12/26',
    card_cvv: '123',
  });

  const update = (e) => setForm(f => ({ ...f, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (cartItems.length === 0) return;
    setLoading(true);
    setError('');

    try {
      const res = await api.post('/orders/checkout', {
        shipping_name: form.shipping_name,
        shipping_email: form.shipping_email,
        shipping_address: form.shipping_address,
        shipping_city: form.shipping_city,
        shipping_state: form.shipping_state,
        shipping_zip: form.shipping_zip,
        payment_last4: form.card_number.replace(/\s/g, '').slice(-4),
      });
      navigate(`/order-confirmation/${res.data.order_number}`);
    } catch (err) {
      setError(err.response?.data?.error || 'Checkout failed. Please try again.');
      setLoading(false);
    }
  };

  if (cartItems.length === 0) {
    return (
      <div className="container" style={{ paddingTop: '3rem', textAlign: 'center' }}>
        <h2>Your cart is empty</h2>
        <Link to="/shop" className="btn btn-primary" style={{ marginTop: '1rem' }}>Go Shopping</Link>
      </div>
    );
  }

  return (
    <div className="checkout-page">
      <div className="page-header">
        <div className="container">
          <h1>Checkout</h1>
          <p>Complete your order below</p>
        </div>
      </div>

      <div className="container checkout-layout">
        <form onSubmit={handleSubmit} className="checkout-form">
          {/* Shipping */}
          <div className="checkout-section card">
            <h2>📦 Shipping Information</h2>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input name="shipping_name" value={form.shipping_name} onChange={update} required className="form-input" placeholder="Jane Doe" />
              </div>
              <div className="form-group">
                <label className="form-label">Email Address</label>
                <input name="shipping_email" type="email" value={form.shipping_email} onChange={update} required className="form-input" placeholder="jane@example.com" />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Street Address</label>
              <input name="shipping_address" value={form.shipping_address} onChange={update} required className="form-input" placeholder="123 Safari Drive" />
            </div>
            <div className="form-row form-row-3">
              <div className="form-group">
                <label className="form-label">City</label>
                <input name="shipping_city" value={form.shipping_city} onChange={update} required className="form-input" placeholder="Wildwood" />
              </div>
              <div className="form-group">
                <label className="form-label">State</label>
                <input name="shipping_state" value={form.shipping_state} onChange={update} required className="form-input" placeholder="WI" maxLength={2} />
              </div>
              <div className="form-group">
                <label className="form-label">ZIP Code</label>
                <input name="shipping_zip" value={form.shipping_zip} onChange={update} required className="form-input" placeholder="53001" />
              </div>
            </div>
          </div>

          {/* Payment */}
          <div className="checkout-section card">
            <h2>💳 Payment Information</h2>
            <div className="fake-payment-notice">
              🔒 This is a simulated store. No real payment will be charged.
            </div>
            <div className="form-group">
              <label className="form-label">Name on Card</label>
              <input name="card_name" value={form.card_name} onChange={update} required className="form-input" placeholder="Jane Doe" />
            </div>
            <div className="form-group">
              <label className="form-label">Card Number</label>
              <input name="card_number" value={form.card_number} onChange={update} required className="form-input" placeholder="4111 1111 1111 1111" maxLength={19} />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Expiry Date</label>
                <input name="card_expiry" value={form.card_expiry} onChange={update} required className="form-input" placeholder="MM/YY" maxLength={5} />
              </div>
              <div className="form-group">
                <label className="form-label">CVV</label>
                <input name="card_cvv" value={form.card_cvv} onChange={update} required className="form-input" placeholder="123" maxLength={4} />
              </div>
            </div>
          </div>

          {error && <div className="alert alert-error">{error}</div>}

          <button type="submit" disabled={loading} className="btn btn-primary btn-lg place-order-btn">
            {loading ? 'Placing Order...' : `Place Order — $${total.toFixed(2)}`}
          </button>
        </form>

        {/* Order summary */}
        <div className="checkout-summary card">
          <h2>Order Summary</h2>
          <div className="summary-items">
            {cartItems.map(item => (
              <div key={item.id} className="summary-item">
                <span className="summary-item-name">{item.name} × {item.quantity}</span>
                <span className="summary-item-price">${(item.price * item.quantity).toFixed(2)}</span>
              </div>
            ))}
          </div>
          <div className="summary-divider" />
          <div className="summary-row"><span>Subtotal</span><span>${subtotal.toFixed(2)}</span></div>
          <div className="summary-row"><span>Tax (8%)</span><span>${tax.toFixed(2)}</span></div>
          <div className="summary-row"><span>Shipping</span><span>{shipping === 0 ? 'FREE' : `$${shipping.toFixed(2)}`}</span></div>
          <div className="summary-divider" />
          <div className="summary-row summary-total"><span>Total</span><strong>${total.toFixed(2)}</strong></div>
        </div>
      </div>
    </div>
  );
}

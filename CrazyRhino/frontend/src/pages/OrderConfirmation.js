import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api';
import './OrderConfirmation.css';

export default function OrderConfirmation() {
  const { orderNumber } = useParams();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/orders/${orderNumber}`).then(res => {
      setOrder(res.data);
    }).finally(() => setLoading(false));
  }, [orderNumber]);

  if (loading) return <div className="loading">Loading order details...</div>;
  if (!order) return <div className="container" style={{ paddingTop: '3rem' }}><p>Order not found.</p></div>;

  const statusColors = {
    confirmed: 'badge-green',
    processing: 'badge-blue',
    shipped: 'badge-amber',
    delivered: 'badge-green',
    cancelled: 'badge-red',
  };

  return (
    <div className="confirm-page container">
      <div className="confirm-hero">
        <div className="confirm-check">✅</div>
        <h1>Order Confirmed!</h1>
        <p>Thank you for your order. A confirmation has been sent to <strong>{order.shipping_email}</strong>.</p>
        <div className="order-number-badge">Order #{order.order_number}</div>
      </div>

      <div className="confirm-layout">
        <div className="confirm-details card">
          <h2>Order Details</h2>
          <div className="detail-row">
            <span>Order Number</span>
            <strong>{order.order_number}</strong>
          </div>
          <div className="detail-row">
            <span>Status</span>
            <span className={`badge ${statusColors[order.status] || 'badge-green'}`}>{order.status}</span>
          </div>
          <div className="detail-row">
            <span>Date</span>
            <span>{new Date(order.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</span>
          </div>
          <div className="detail-row">
            <span>Payment</span>
            <span>**** **** **** {order.payment_last4}</span>
          </div>

          <div className="confirm-divider" />
          <h3>Items Ordered</h3>
          {order.items.map(item => (
            <div key={item.id} className="order-item-row">
              <span className="order-item-name">{item.product_name}</span>
              <span className="order-item-qty">× {item.quantity}</span>
              <span className="order-item-price">${(item.unit_price * item.quantity).toFixed(2)}</span>
            </div>
          ))}

          <div className="confirm-divider" />
          <div className="totals">
            <div className="total-row"><span>Subtotal</span><span>${order.subtotal.toFixed(2)}</span></div>
            <div className="total-row"><span>Tax</span><span>${order.tax.toFixed(2)}</span></div>
            <div className="total-row total-grand"><span>Total</span><strong>${order.total.toFixed(2)}</strong></div>
          </div>
        </div>

        <div className="confirm-shipping card">
          <h2>Shipping To</h2>
          <div className="shipping-block">
            <strong>{order.shipping_name}</strong>
            <p>{order.shipping_address}</p>
            <p>{order.shipping_city}, {order.shipping_state} {order.shipping_zip}</p>
          </div>

          <div className="confirm-divider" />
          <h2>What's Next?</h2>
          <div className="next-steps">
            <div className="next-step">
              <span>📧</span>
              <div>
                <strong>Confirmation Email</strong>
                <p>Sent to {order.shipping_email}</p>
              </div>
            </div>
            <div className="next-step">
              <span>📦</span>
              <div>
                <strong>Processing</strong>
                <p>Your order will ship within 2-3 business days</p>
              </div>
            </div>
            <div className="next-step">
              <span>🚚</span>
              <div>
                <strong>Delivery</strong>
                <p>Estimated 5-7 business days</p>
              </div>
            </div>
          </div>

          <div className="confirm-actions">
            <Link to="/orders" className="btn btn-outline" style={{ width: '100%' }}>View All Orders</Link>
            <Link to="/shop" className="btn btn-primary" style={{ width: '100%' }}>Continue Shopping</Link>
          </div>
        </div>
      </div>
    </div>
  );
}

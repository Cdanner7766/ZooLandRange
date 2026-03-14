import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import './Orders.css';

const STATUS_BADGE = {
  confirmed: 'badge-green',
  processing: 'badge-blue',
  shipped: 'badge-amber',
  delivered: 'badge-green',
  cancelled: 'badge-red',
};

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/orders').then(res => setOrders(res.data)).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading orders...</div>;

  return (
    <div className="orders-page">
      <div className="page-header">
        <div className="container">
          <h1>My Orders</h1>
          <p>Track and review your order history</p>
        </div>
      </div>

      <div className="container" style={{ paddingTop: '1.5rem', paddingBottom: '3rem' }}>
        {orders.length === 0 ? (
          <div className="empty-state">
            <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>📦</div>
            <h3>No orders yet</h3>
            <p>When you place an order, it will appear here.</p>
            <Link to="/shop" className="btn btn-primary" style={{ marginTop: '1.5rem' }}>Start Shopping</Link>
          </div>
        ) : (
          <div className="orders-list">
            {orders.map(order => (
              <div key={order.id} className="order-card card">
                <div className="order-header">
                  <div>
                    <div className="order-number">Order #{order.order_number}</div>
                    <div className="order-date">{new Date(order.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <span className={`badge ${STATUS_BADGE[order.status] || 'badge-green'}`}>{order.status}</span>
                    <div className="order-total">${order.total.toFixed(2)}</div>
                  </div>
                </div>
                <div className="order-items-preview">
                  {order.items.slice(0, 3).map(item => (
                    <span key={item.id} className="item-pill">
                      {item.product_name} × {item.quantity}
                    </span>
                  ))}
                  {order.items.length > 3 && (
                    <span className="item-pill item-pill-more">+{order.items.length - 3} more</span>
                  )}
                </div>
                <div className="order-footer">
                  <Link to={`/order-confirmation/${order.order_number}`} className="btn btn-outline btn-sm">
                    View Details
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

import React, { useEffect, useState } from 'react';
import api from '../api';
import './Admin.css';

const STATUS_OPTIONS = ['confirmed', 'processing', 'shipped', 'delivered', 'cancelled'];
const STATUS_BADGE = {
  confirmed: 'badge-green', processing: 'badge-blue',
  shipped: 'badge-amber', delivered: 'badge-green', cancelled: 'badge-red',
};

export default function Admin() {
  const [tab, setTab] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showProductForm, setShowProductForm] = useState(false);
  const [productForm, setProductForm] = useState({ name: '', description: '', price: '', category: 'merchandise', stock: 100 });
  const [formError, setFormError] = useState('');
  const [formSuccess, setFormSuccess] = useState('');

  useEffect(() => {
    if (tab === 'dashboard') loadStats();
    else if (tab === 'products') loadProducts();
    else if (tab === 'orders') loadOrders();
    else if (tab === 'users') loadUsers();
  }, [tab]);

  const loadStats = () => { setLoading(true); api.get('/admin/stats').then(r => setStats(r.data)).finally(() => setLoading(false)); };
  const loadProducts = () => { setLoading(true); api.get('/admin/products').then(r => setProducts(r.data)).finally(() => setLoading(false)); };
  const loadOrders = () => { setLoading(true); api.get('/admin/orders').then(r => setOrders(r.data)).finally(() => setLoading(false)); };
  const loadUsers = () => { setLoading(true); api.get('/admin/users').then(r => setUsers(r.data)).finally(() => setLoading(false)); };

  const handleAddProduct = async (e) => {
    e.preventDefault();
    setFormError(''); setFormSuccess('');
    try {
      await api.post('/admin/products', { ...productForm, price: parseFloat(productForm.price), stock: parseInt(productForm.stock) });
      setFormSuccess('Product added!');
      setProductForm({ name: '', description: '', price: '', category: 'merchandise', stock: 100 });
      setShowProductForm(false);
      loadProducts();
    } catch (err) {
      setFormError(err.response?.data?.error || 'Failed to add product');
    }
  };

  const handleToggleProduct = async (p) => {
    await api.put(`/admin/products/${p.id}`, { active: p.active ? 0 : 1 });
    loadProducts();
  };

  const handleOrderStatus = async (orderId, status) => {
    await api.put(`/admin/orders/${orderId}/status`, { status });
    loadOrders();
  };

  return (
    <div className="admin-page">
      <div className="admin-header">
        <div className="container">
          <h1>🔧 Admin Panel</h1>
          <p>Wild Kingdom Zoo Store Management</p>
        </div>
      </div>

      <div className="container admin-layout">
        <nav className="admin-nav">
          {[
            { key: 'dashboard', label: '📊 Dashboard' },
            { key: 'products', label: '🛍️ Products' },
            { key: 'orders', label: '📦 Orders' },
            { key: 'users', label: '👥 Users' },
          ].map(t => (
            <button key={t.key} className={`admin-tab ${tab === t.key ? 'active' : ''}`} onClick={() => setTab(t.key)}>
              {t.label}
            </button>
          ))}
        </nav>

        <div className="admin-content">
          {loading && <div className="loading">Loading...</div>}

          {/* Dashboard */}
          {tab === 'dashboard' && stats && !loading && (
            <div>
              <h2>Dashboard</h2>
              <div className="stats-grid">
                <div className="stat-card"><div className="stat-value">{stats.totalOrders}</div><div className="stat-label">Total Orders</div></div>
                <div className="stat-card green"><div className="stat-value">${stats.totalRevenue.toFixed(2)}</div><div className="stat-label">Total Revenue</div></div>
                <div className="stat-card blue"><div className="stat-value">{stats.totalUsers}</div><div className="stat-label">Customers</div></div>
                <div className="stat-card amber"><div className="stat-value">{stats.totalProducts}</div><div className="stat-label">Active Products</div></div>
              </div>

              <h3 style={{ marginTop: '2rem', marginBottom: '1rem' }}>Recent Orders</h3>
              <div className="admin-table-wrap">
                <table className="admin-table">
                  <thead><tr><th>Order</th><th>Customer</th><th>Total</th><th>Status</th><th>Date</th></tr></thead>
                  <tbody>
                    {stats.recentOrders.map(o => (
                      <tr key={o.id}>
                        <td><code>{o.order_number}</code></td>
                        <td>{o.username}</td>
                        <td>${o.total.toFixed(2)}</td>
                        <td><span className={`badge ${STATUS_BADGE[o.status]}`}>{o.status}</span></td>
                        <td>{new Date(o.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Products */}
          {tab === 'products' && !loading && (
            <div>
              <div className="section-bar">
                <h2>Products ({products.length})</h2>
                <button className="btn btn-primary btn-sm" onClick={() => setShowProductForm(!showProductForm)}>
                  {showProductForm ? 'Cancel' : '+ Add Product'}
                </button>
              </div>

              {showProductForm && (
                <form onSubmit={handleAddProduct} className="card admin-form">
                  <h3>Add New Product</h3>
                  {formError && <div className="alert alert-error">{formError}</div>}
                  {formSuccess && <div className="alert alert-success">{formSuccess}</div>}
                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label">Name</label>
                      <input className="form-input" required value={productForm.name} onChange={e => setProductForm(f => ({ ...f, name: e.target.value }))} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Category</label>
                      <select className="form-input" value={productForm.category} onChange={e => setProductForm(f => ({ ...f, category: e.target.value }))}>
                        <option value="merchandise">Merchandise</option>
                        <option value="tickets">Tickets</option>
                      </select>
                    </div>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Description</label>
                    <textarea className="form-input" rows={2} value={productForm.description} onChange={e => setProductForm(f => ({ ...f, description: e.target.value }))} />
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label">Price ($)</label>
                      <input className="form-input" type="number" step="0.01" required value={productForm.price} onChange={e => setProductForm(f => ({ ...f, price: e.target.value }))} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Stock</label>
                      <input className="form-input" type="number" value={productForm.stock} onChange={e => setProductForm(f => ({ ...f, stock: e.target.value }))} />
                    </div>
                  </div>
                  <button type="submit" className="btn btn-primary">Save Product</button>
                </form>
              )}

              <div className="admin-table-wrap">
                <table className="admin-table">
                  <thead><tr><th>ID</th><th>Name</th><th>Category</th><th>Price</th><th>Stock</th><th>Status</th><th>Action</th></tr></thead>
                  <tbody>
                    {products.map(p => (
                      <tr key={p.id} className={!p.active ? 'inactive-row' : ''}>
                        <td>{p.id}</td>
                        <td>{p.name}</td>
                        <td><span className={`badge ${p.category === 'tickets' ? 'badge-blue' : 'badge-amber'}`}>{p.category}</span></td>
                        <td>${p.price.toFixed(2)}</td>
                        <td>{p.stock}</td>
                        <td><span className={`badge ${p.active ? 'badge-green' : 'badge-red'}`}>{p.active ? 'Active' : 'Hidden'}</span></td>
                        <td>
                          <button className={`btn btn-sm ${p.active ? 'btn-danger' : 'btn-primary'}`} onClick={() => handleToggleProduct(p)}>
                            {p.active ? 'Hide' : 'Show'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Orders */}
          {tab === 'orders' && !loading && (
            <div>
              <h2>Orders ({orders.length})</h2>
              <div className="admin-table-wrap">
                <table className="admin-table">
                  <thead><tr><th>Order #</th><th>Customer</th><th>Total</th><th>Items</th><th>Status</th><th>Date</th></tr></thead>
                  <tbody>
                    {orders.map(o => (
                      <tr key={o.id}>
                        <td><code style={{ fontSize: '0.8rem' }}>{o.order_number}</code></td>
                        <td>{o.username}</td>
                        <td>${o.total.toFixed(2)}</td>
                        <td>{o.items.length} item{o.items.length !== 1 ? 's' : ''}</td>
                        <td>
                          <select
                            className="status-select"
                            value={o.status}
                            onChange={e => handleOrderStatus(o.id, e.target.value)}
                          >
                            {STATUS_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
                          </select>
                        </td>
                        <td>{new Date(o.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Users */}
          {tab === 'users' && !loading && (
            <div>
              <h2>Users ({users.length})</h2>
              <div className="admin-table-wrap">
                <table className="admin-table">
                  <thead><tr><th>ID</th><th>Username</th><th>Email</th><th>Role</th><th>Joined</th></tr></thead>
                  <tbody>
                    {users.map(u => (
                      <tr key={u.id}>
                        <td>{u.id}</td>
                        <td><strong>{u.username}</strong></td>
                        <td>{u.email}</td>
                        <td><span className={`badge ${u.role === 'admin' ? 'badge-amber' : 'badge-green'}`}>{u.role}</span></td>
                        <td>{new Date(u.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

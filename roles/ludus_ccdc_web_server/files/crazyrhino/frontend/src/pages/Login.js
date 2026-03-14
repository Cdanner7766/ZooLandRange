import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import './Auth.css';

export default function Login() {
  const { login } = useAuth();
  const { fetchCart } = useCart();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const update = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await api.post('/auth/login', form);
      login(res.data.token, res.data.user);
      await fetchCart();
      navigate(res.data.user.role === 'admin' ? '/admin' : '/');
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed');
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card card">
        <div className="auth-logo">🦁</div>
        <h1>Welcome Back</h1>
        <p className="auth-sub">Sign in to your Wild Kingdom account</p>

        <div className="demo-creds">
          <strong>Demo accounts:</strong><br />
          Customer: <code>johndoe / password123</code><br />
          Admin: <code>admin / admin123</code>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Username or Email</label>
            <input name="username" value={form.username} onChange={update} required className="form-input" placeholder="johndoe" autoFocus />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input name="password" type="password" value={form.password} onChange={update} required className="form-input" placeholder="••••••••" />
          </div>
          <button type="submit" disabled={loading} className="btn btn-primary btn-lg auth-btn">
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="auth-switch">
          Don't have an account? <Link to="/register">Sign up free</Link>
        </p>
      </div>
    </div>
  );
}

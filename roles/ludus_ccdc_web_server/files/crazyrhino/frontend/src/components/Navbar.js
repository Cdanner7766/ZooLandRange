import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import './Navbar.css';

export default function Navbar() {
  const { user, logout } = useAuth();
  const { cartCount } = useCart();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
    setMenuOpen(false);
  };

  return (
    <nav className="navbar">
      <div className="nav-container">
        <Link to="/" className="nav-logo">
          <span className="logo-icon">🦁</span>
          <div>
            <div className="logo-name">Wild Kingdom</div>
            <div className="logo-sub">Zoo Store</div>
          </div>
        </Link>

        <div className="nav-links">
          <Link to="/" className="nav-link">Home</Link>
          <Link to="/shop" className="nav-link">Shop</Link>
          <Link to="/shop/merchandise" className="nav-link">Merchandise</Link>
          <Link to="/shop/tickets" className="nav-link">Tickets</Link>
        </div>

        <div className="nav-actions">
          {user ? (
            <>
              {user.role === 'admin' && (
                <Link to="/admin" className="nav-link admin-link">Admin</Link>
              )}
              <Link to="/orders" className="nav-link">My Orders</Link>
              <span className="nav-username">Hi, {user.username}!</span>
              <button onClick={handleLogout} className="btn btn-outline btn-sm">Logout</button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn btn-outline btn-sm">Login</Link>
              <Link to="/register" className="btn btn-primary btn-sm">Sign Up</Link>
            </>
          )}
          <Link to="/cart" className="cart-btn">
            🛒
            {cartCount > 0 && <span className="cart-badge">{cartCount}</span>}
          </Link>
        </div>

        <button className="hamburger" onClick={() => setMenuOpen(!menuOpen)}>
          {menuOpen ? '✕' : '☰'}
        </button>
      </div>

      {menuOpen && (
        <div className="mobile-menu">
          <Link to="/" className="mobile-link" onClick={() => setMenuOpen(false)}>Home</Link>
          <Link to="/shop" className="mobile-link" onClick={() => setMenuOpen(false)}>Shop All</Link>
          <Link to="/shop/merchandise" className="mobile-link" onClick={() => setMenuOpen(false)}>Merchandise</Link>
          <Link to="/shop/tickets" className="mobile-link" onClick={() => setMenuOpen(false)}>Tickets & Experiences</Link>
          {user ? (
            <>
              <Link to="/orders" className="mobile-link" onClick={() => setMenuOpen(false)}>My Orders</Link>
              {user.role === 'admin' && <Link to="/admin" className="mobile-link" onClick={() => setMenuOpen(false)}>Admin Panel</Link>}
              <button onClick={handleLogout} className="mobile-link mobile-logout">Logout</button>
            </>
          ) : (
            <>
              <Link to="/login" className="mobile-link" onClick={() => setMenuOpen(false)}>Login</Link>
              <Link to="/register" className="mobile-link" onClick={() => setMenuOpen(false)}>Sign Up</Link>
            </>
          )}
          <Link to="/cart" className="mobile-link" onClick={() => setMenuOpen(false)}>Cart ({cartCount})</Link>
        </div>
      )}
    </nav>
  );
}

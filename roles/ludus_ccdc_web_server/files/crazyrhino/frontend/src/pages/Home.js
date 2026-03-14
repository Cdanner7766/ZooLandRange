import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import ProductCard from '../components/ProductCard';
import './Home.css';

export default function Home() {
  const [featured, setFeatured] = useState([]);

  useEffect(() => {
    api.get('/products').then(res => {
      const shuffled = res.data.sort(() => 0.5 - Math.random());
      setFeatured(shuffled.slice(0, 8));
    }).catch(() => {});
  }, []);

  return (
    <div className="home">
      {/* Hero */}
      <section className="hero">
        <div className="hero-content">
          <div className="hero-badge">🌿 Now Open Year-Round</div>
          <h1>Wild Kingdom<br /><span>Zoo Store</span></h1>
          <p>Shop exclusive merchandise and book unforgettable animal experiences — all from the comfort of home.</p>
          <div className="hero-actions">
            <Link to="/shop/tickets" className="btn btn-amber btn-lg">Book Tickets 🎟️</Link>
            <Link to="/shop/merchandise" className="btn btn-outline-white btn-lg">Shop Merch 👕</Link>
          </div>
        </div>
        <div className="hero-animals">
          <span>🦁</span><span>🐘</span><span>🦒</span><span>🐧</span><span>🐯</span>
        </div>
      </section>

      {/* Category cards */}
      <section className="categories container">
        <Link to="/shop/merchandise" className="cat-card merch">
          <div className="cat-icon">👕</div>
          <h2>Merchandise</h2>
          <p>T-shirts, plushies, hats, accessories, and more</p>
          <span className="cat-cta">Shop Now →</span>
        </Link>
        <Link to="/shop/tickets" className="cat-card tickets">
          <div className="cat-icon">🎟️</div>
          <h2>Tickets & Experiences</h2>
          <p>Day passes, memberships, VIP tours, and animal encounters</p>
          <span className="cat-cta">Book Now →</span>
        </Link>
      </section>

      {/* Features strip */}
      <section className="features container">
        <div className="feature">
          <span>🔒</span>
          <div>
            <strong>Secure Checkout</strong>
            <p>Your data is safe with us</p>
          </div>
        </div>
        <div className="feature">
          <span>📦</span>
          <div>
            <strong>Free Shipping</strong>
            <p>On orders over $50</p>
          </div>
        </div>
        <div className="feature">
          <span>📱</span>
          <div>
            <strong>Digital Tickets</strong>
            <p>Delivered to your inbox instantly</p>
          </div>
        </div>
        <div className="feature">
          <span>♻️</span>
          <div>
            <strong>Eco-Friendly</strong>
            <p>Sustainably sourced products</p>
          </div>
        </div>
      </section>

      {/* Featured products */}
      <section className="featured container">
        <div className="section-header">
          <h2>Featured Products</h2>
          <Link to="/shop" className="see-all">See All →</Link>
        </div>
        <div className="product-grid">
          {featured.map(p => <ProductCard key={p.id} product={p} compact />)}
        </div>
      </section>

      {/* CTA Banner */}
      <section className="cta-banner">
        <div className="container">
          <div className="cta-content">
            <h2>Plan Your Wild Kingdom Adventure</h2>
            <p>From single-day visits to full year memberships — we have the perfect pass for you.</p>
            <Link to="/shop/tickets" className="btn btn-amber btn-lg">View All Tickets</Link>
          </div>
          <div className="cta-animals">🐧 🦁 🐘 🦒 🐯 🐼</div>
        </div>
      </section>
    </div>
  );
}

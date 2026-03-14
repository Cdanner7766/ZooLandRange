import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api';
import ProductCard from '../components/ProductCard';
import './Shop.css';

export default function Shop() {
  const { category } = useParams();
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [activeCategory, setActiveCategory] = useState(category || 'all');

  useEffect(() => {
    setActiveCategory(category || 'all');
  }, [category]);

  useEffect(() => {
    setLoading(true);
    const params = {};
    if (activeCategory !== 'all') params.category = activeCategory;
    if (search) params.search = search;

    api.get('/products', { params }).then(res => {
      setProducts(res.data);
    }).catch(() => {
      setProducts([]);
    }).finally(() => setLoading(false));
  }, [activeCategory, search]);

  const handleCategoryChange = (cat) => {
    setActiveCategory(cat);
    navigate(cat === 'all' ? '/shop' : `/shop/${cat}`, { replace: true });
  };

  return (
    <div className="shop-page">
      <div className="page-header">
        <div className="container">
          <h1>
            {activeCategory === 'merchandise' ? '🛍️ Merchandise' :
             activeCategory === 'tickets' ? '🎟️ Tickets & Experiences' :
             '🦁 All Products'}
          </h1>
          <p>
            {activeCategory === 'merchandise' ? 'Take home a piece of Wild Kingdom with our exclusive merch' :
             activeCategory === 'tickets' ? 'Book your unforgettable zoo experience today' :
             'Browse all merchandise, tickets, and animal experiences'}
          </p>
        </div>
      </div>

      <div className="container shop-container">
        <div className="shop-toolbar">
          <div className="category-tabs">
            {[
              { key: 'all', label: '🌿 All Products' },
              { key: 'merchandise', label: '👕 Merchandise' },
              { key: 'tickets', label: '🎟️ Tickets & Experiences' },
            ].map(tab => (
              <button
                key={tab.key}
                className={`tab-btn ${activeCategory === tab.key ? 'active' : ''}`}
                onClick={() => handleCategoryChange(tab.key)}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <div className="search-box">
            <input
              type="text"
              placeholder="Search products..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="form-input search-input"
            />
          </div>
        </div>

        {loading ? (
          <div className="loading">Loading products...</div>
        ) : products.length === 0 ? (
          <div className="empty-state">
            <h3>No products found</h3>
            <p>Try adjusting your search or category filter.</p>
          </div>
        ) : (
          <>
            <p className="result-count">{products.length} product{products.length !== 1 ? 's' : ''} found</p>
            <div className="product-grid shop-grid">
              {products.map(p => <ProductCard key={p.id} product={p} />)}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

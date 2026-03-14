import React from 'react';
import { Link } from 'react-router-dom';
import './Footer.css';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-brand">
          <div className="footer-logo">🦁 Wild Kingdom Zoo</div>
          <p>Your favorite destination for wildlife, wonder, and adventure. Visit us or shop online!</p>
          <p className="footer-note">Open daily 9am – 5pm · 1 Safari Drive, Wildwood, WI 53001</p>
        </div>

        <div className="footer-links">
          <h4>Shop</h4>
          <Link to="/shop/merchandise">Merchandise</Link>
          <Link to="/shop/tickets">Tickets & Experiences</Link>
          <Link to="/shop">Browse All</Link>
        </div>

        <div className="footer-links">
          <h4>Account</h4>
          <Link to="/login">Login</Link>
          <Link to="/register">Sign Up</Link>
          <Link to="/orders">Order History</Link>
        </div>

        <div className="footer-links">
          <h4>Visit</h4>
          <a href="#hours">Hours & Admission</a>
          <a href="#map">Zoo Map</a>
          <a href="#contact">Contact Us</a>
        </div>
      </div>
      <div className="footer-bottom">
        <p>© 2024 Wild Kingdom Zoo. All rights reserved. This is a simulated e-commerce environment.</p>
      </div>
    </footer>
  );
}

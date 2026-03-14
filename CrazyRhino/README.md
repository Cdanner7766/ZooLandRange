# Wild Kingdom Zoo Online Store

A fake-but-functional zoo e-commerce store built for Ludus Cyber Range deployment.

## Stack
- **Frontend**: React 18, React Router, Axios
- **Backend**: Node.js, Express, better-sqlite3
- **Database**: SQLite (file-based, zero config)
- **Auth**: JWT + bcrypt

## Features
- Product catalog (Zoo Merchandise + Tickets & Experiences)
- User registration & JWT login
- Server-side shopping cart
- Checkout with fake payment form
- Order history per user
- Admin panel (products, orders, users, stats)

## Demo Accounts
| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Customer | `johndoe` | `password123` |

## Quick Start (Local Dev)

```bash
# Backend
cd backend
npm install
npm start        # runs on :5000

# Frontend (new terminal)
cd frontend
npm install
npm start        # runs on :3000, proxies /api → :5000
```

## Docker Deploy

```bash
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:5000/api

## Ludus Cyber Range Notes
- Change `JWT_SECRET` in `docker-compose.yml` for production
- The `zoo_data` Docker volume persists the SQLite database across restarts
- All products auto-seed on first boot
- No real payment processing — card data is fake

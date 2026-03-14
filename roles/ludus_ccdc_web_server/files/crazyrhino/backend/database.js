const Database = require('better-sqlite3');
const bcrypt = require('bcryptjs');
const path = require('path');

const DB_PATH = process.env.DB_PATH || path.join(__dirname, 'zoo_store.db');

let db;

function getDb() {
  if (!db) {
    db = new Database(DB_PATH);
    db.pragma('journal_mode = WAL');
    db.pragma('foreign_keys = ON');
  }
  return db;
}

function initDb() {
  const db = getDb();

  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      email TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'customer',
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS products (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      description TEXT,
      price REAL NOT NULL,
      category TEXT NOT NULL,
      image_url TEXT,
      stock INTEGER NOT NULL DEFAULT 100,
      active INTEGER NOT NULL DEFAULT 1,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS cart_items (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      product_id INTEGER NOT NULL,
      quantity INTEGER NOT NULL DEFAULT 1,
      added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
      FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
      UNIQUE(user_id, product_id)
    );

    CREATE TABLE IF NOT EXISTS orders (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      order_number TEXT UNIQUE NOT NULL,
      status TEXT NOT NULL DEFAULT 'confirmed',
      subtotal REAL NOT NULL,
      tax REAL NOT NULL,
      total REAL NOT NULL,
      shipping_name TEXT NOT NULL,
      shipping_email TEXT NOT NULL,
      shipping_address TEXT NOT NULL,
      shipping_city TEXT NOT NULL,
      shipping_state TEXT NOT NULL,
      shipping_zip TEXT NOT NULL,
      payment_last4 TEXT NOT NULL DEFAULT '4242',
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS order_items (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      order_id INTEGER NOT NULL,
      product_id INTEGER NOT NULL,
      product_name TEXT NOT NULL,
      quantity INTEGER NOT NULL,
      unit_price REAL NOT NULL,
      FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
    );
  `);

  seedData(db);
}

function seedData(db) {
  const adminExists = db.prepare('SELECT id FROM users WHERE role = ?').get('admin');
  if (!adminExists) {
    const adminHash = bcrypt.hashSync('admin123', 10);
    const userHash = bcrypt.hashSync('password123', 10);
    db.prepare('INSERT OR IGNORE INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)').run('admin', 'admin@wildkingdomzoo.com', adminHash, 'admin');
    db.prepare('INSERT OR IGNORE INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)').run('johndoe', 'john@example.com', userHash, 'customer');
  }

  const productCount = db.prepare('SELECT COUNT(*) as count FROM products').get();
  if (productCount.count === 0) {
    const products = [
      // Merchandise
      { name: 'Lion Pride T-Shirt', description: 'Soft cotton tee featuring our majestic African lion family. Available in sizes S-XXL.', price: 24.99, category: 'merchandise', image_url: '/images/lion-tshirt.jpg', stock: 150 },
      { name: 'Penguin Parade Hoodie', description: 'Stay warm like our Antarctic friends! Cozy pullover hoodie with penguin embroidery.', price: 49.99, category: 'merchandise', image_url: '/images/penguin-hoodie.jpg', stock: 80 },
      { name: 'Wild Kingdom Baseball Cap', description: 'Classic adjustable cap with Wild Kingdom Zoo embroidered logo. One size fits all.', price: 18.99, category: 'merchandise', image_url: '/images/zoo-cap.jpg', stock: 200 },
      { name: 'Elephant Plush Toy (Large)', description: 'Huggable 18-inch stuffed elephant, perfect for zoo fans of all ages.', price: 29.99, category: 'merchandise', image_url: '/images/elephant-plush.jpg', stock: 120 },
      { name: 'Giraffe Plush Toy (Small)', description: 'Adorable 10-inch giraffe plushie with realistic spots and long neck.', price: 14.99, category: 'merchandise', image_url: '/images/giraffe-plush.jpg', stock: 180 },
      { name: 'Zoo Animal Keychain Set', description: 'Set of 6 mini animal keychains: lion, elephant, giraffe, penguin, tiger, and panda.', price: 12.99, category: 'merchandise', image_url: '/images/keychain-set.jpg', stock: 300 },
      { name: 'Wild Kingdom Tote Bag', description: 'Eco-friendly canvas tote bag featuring a colorful animal print. Great for shopping!', price: 15.99, category: 'merchandise', image_url: '/images/tote-bag.jpg', stock: 250 },
      { name: 'Tiger Stripe Water Bottle', description: '20oz insulated stainless steel water bottle with tiger stripe pattern. Keeps drinks cold 24hrs.', price: 34.99, category: 'merchandise', image_url: '/images/water-bottle.jpg', stock: 90 },
      { name: 'Zoo Animal Coloring Book', description: '48-page coloring book featuring 40 detailed animal illustrations from our zoo.', price: 8.99, category: 'merchandise', image_url: '/images/coloring-book.jpg', stock: 400 },
      { name: 'Panda Bear Snapback Hat', description: 'Trendy snapback with embroidered panda face on the front. One size fits most.', price: 22.99, category: 'merchandise', image_url: '/images/panda-hat.jpg', stock: 110 },
      { name: 'Safari Explorer Kids Backpack', description: 'Durable kids backpack with animal print and fun safari explorer patches.', price: 39.99, category: 'merchandise', image_url: '/images/kids-backpack.jpg', stock: 60 },
      { name: 'Wild Kingdom Snow Globe', description: 'Beautiful collectible snow globe featuring miniature zoo animals inside.', price: 19.99, category: 'merchandise', image_url: '/images/snow-globe.jpg', stock: 75 },
      // Tickets
      { name: 'General Admission - Adult', description: 'Full day access to all exhibits, shows, and general zoo areas. Valid any day.', price: 34.99, category: 'tickets', image_url: '/images/ticket-adult.jpg', stock: 9999 },
      { name: 'General Admission - Child (3-12)', description: 'Full day access for children ages 3-12. Children under 3 are always free!', price: 19.99, category: 'tickets', image_url: '/images/ticket-child.jpg', stock: 9999 },
      { name: 'General Admission - Senior (65+)', description: 'Full day access for senior guests 65 and older. Valid any day.', price: 24.99, category: 'tickets', image_url: '/images/ticket-senior.jpg', stock: 9999 },
      { name: 'Annual Membership - Individual', description: 'Unlimited visits for one adult for a full year plus 10% off all merchandise and dining.', price: 89.99, category: 'tickets', image_url: '/images/membership-individual.jpg', stock: 9999 },
      { name: 'Annual Membership - Family (2+2)', description: 'Unlimited visits for 2 adults and 2 children for one year. Best value for families!', price: 149.99, category: 'tickets', image_url: '/images/membership-family.jpg', stock: 9999 },
      { name: 'Behind-the-Scenes Safari Tour', description: 'Exclusive 90-minute guided tour of non-public areas. Meet keepers and animals up close. Ages 8+.', price: 79.99, category: 'tickets', image_url: '/images/safari-tour.jpg', stock: 500 },
      { name: 'Penguin Encounter Experience', description: 'Get up close with our penguin colony! 30-minute guided interaction session. Ages 5+.', price: 59.99, category: 'tickets', image_url: '/images/penguin-encounter.jpg', stock: 300 },
      { name: 'Elephant Feeding Session', description: 'Feed our gentle giants under keeper supervision. 45-minute experience. Ages 6+.', price: 49.99, category: 'tickets', image_url: '/images/elephant-feeding.jpg', stock: 400 },
      { name: 'VIP All-Access Day Pass', description: 'Premium full-day experience with priority entry, guided tour, two animal encounters, and lunch.', price: 199.99, category: 'tickets', image_url: '/images/vip-pass.jpg', stock: 200 },
      { name: 'Night at the Zoo - Adults Only Event', description: 'Special evening event after hours with live music, food, cocktails, and illuminated exhibits.', price: 54.99, category: 'tickets', image_url: '/images/night-zoo.jpg', stock: 600 },
    ];

    const insert = db.prepare('INSERT INTO products (name, description, price, category, image_url, stock) VALUES (@name, @description, @price, @category, @image_url, @stock)');
    const insertMany = db.transaction((products) => {
      for (const p of products) insert.run(p);
    });
    insertMany(products);
  }
}

module.exports = { getDb, initDb };

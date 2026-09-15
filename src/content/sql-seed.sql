-- Sample database seeded for every SQL session
-- Tables: customers, products, orders, order_items

CREATE TABLE customers (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT,
  city TEXT,
  joined_year INTEGER
);

INSERT INTO customers VALUES
  (1, 'Alice Chen',     'alice@example.com',  'London',    2021),
  (2, 'Bob Patel',      'bob@example.com',    'Manchester',2022),
  (3, 'Carol O''Brien', 'carol@example.com',  'Dublin',    2020),
  (4, 'David Kim',      'david@example.com',  'Edinburgh', 2023),
  (5, 'Eva Johansson',  'eva@example.com',    'London',    2021);

CREATE TABLE products (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT,
  price REAL
);

INSERT INTO products VALUES
  (1, 'Keyboard',   'Electronics', 79.99),
  (2, 'Mouse',      'Electronics', 29.99),
  (3, 'Desk Lamp',  'Furniture',   34.50),
  (4, 'Notebook',   'Stationery',   4.99),
  (5, 'USB Hub',    'Electronics', 19.99),
  (6, 'Chair',      'Furniture',  199.00);

CREATE TABLE orders (
  id INTEGER PRIMARY KEY,
  customer_id INTEGER REFERENCES customers(id),
  order_date TEXT,
  status TEXT
);

INSERT INTO orders VALUES
  (1, 1, '2024-01-15', 'delivered'),
  (2, 2, '2024-02-03', 'delivered'),
  (3, 1, '2024-03-22', 'shipped'),
  (4, 3, '2024-03-30', 'pending'),
  (5, 4, '2024-04-10', 'delivered'),
  (6, 2, '2024-04-15', 'shipped');

CREATE TABLE order_items (
  id INTEGER PRIMARY KEY,
  order_id INTEGER REFERENCES orders(id),
  product_id INTEGER REFERENCES products(id),
  quantity INTEGER,
  unit_price REAL
);

INSERT INTO order_items VALUES
  (1,  1, 1, 1, 79.99),
  (2,  1, 2, 2, 29.99),
  (3,  2, 3, 1, 34.50),
  (4,  3, 5, 1, 19.99),
  (5,  3, 4, 3,  4.99),
  (6,  4, 6, 1,199.00),
  (7,  5, 1, 1, 79.99),
  (8,  5, 2, 1, 29.99),
  (9,  6, 4, 5,  4.99),
  (10, 6, 5, 2, 19.99);

---
course: SQL Basics
language: sql
description: Query and analyse data with SQL — from SELECT to JOINs and aggregates
---

# Lesson: Your First SELECT

SQL (Structured Query Language) is used to query databases. The most basic statement is `SELECT`, which retrieves rows from a table.

The sample database contains four tables: `customers`, `products`, `orders`, and `order_items`. Use `SELECT * FROM <table>` to see all columns.

```sql starter
SELECT * FROM customers;
```

```sql solution
SELECT * FROM customers;
```

# Lesson: Filtering with WHERE

`WHERE` filters rows that match a condition. Combine conditions with `AND` and `OR`.

```sql starter
-- Find all customers in London
SELECT name, city
FROM customers
```

```sql solution
SELECT name, city
FROM customers
WHERE city = 'London';
```

# Lesson: Sorting with ORDER BY

`ORDER BY` sorts the result set. Add `DESC` to reverse the order.

```sql starter
-- List products from cheapest to most expensive
SELECT name, price
FROM products
```

```sql solution
SELECT name, price
FROM products
ORDER BY price ASC;
```

# Lesson: Limiting Results

`LIMIT` caps the number of rows returned — useful for previewing large tables or finding top-N results.

```sql starter
-- Show the 3 most expensive products
SELECT name, price
FROM products
ORDER BY price DESC
```

```sql solution
SELECT name, price
FROM products
ORDER BY price DESC
LIMIT 3;
```

# Lesson: Aggregate Functions

Aggregate functions summarise multiple rows into a single value.

| Function | What it does |
|----------|-------------|
| `COUNT(*)` | Number of rows |
| `SUM(col)` | Total of a numeric column |
| `AVG(col)` | Average |
| `MIN(col)` / `MAX(col)` | Smallest / largest value |

```sql starter
-- How many customers are there, and what is the average product price?
SELECT COUNT(*) FROM customers;
```

```sql solution
SELECT COUNT(*) AS total_customers FROM customers;
SELECT ROUND(AVG(price), 2) AS avg_price FROM products;
SELECT SUM(price) AS total_inventory_value FROM products;
```

# Lesson: GROUP BY

`GROUP BY` groups rows that share a value, then applies an aggregate to each group.

```sql starter
-- Count customers per city
SELECT city
FROM customers
```

```sql solution
SELECT city, COUNT(*) AS num_customers
FROM customers
GROUP BY city
ORDER BY num_customers DESC;
```

# Lesson: INNER JOIN

A `JOIN` combines rows from two tables based on a related column.

`INNER JOIN` returns only rows that have a match in both tables.

```sql starter
-- Show each order alongside the customer's name
SELECT orders.id, orders.order_date
FROM orders
```

```sql solution
SELECT orders.id, customers.name, orders.order_date, orders.status
FROM orders
INNER JOIN customers ON orders.customer_id = customers.id
ORDER BY orders.order_date;
```

# Lesson: LEFT JOIN

A `LEFT JOIN` returns all rows from the left table, with matching rows from the right table — `NULL` where there is no match.

```sql setup
-- Add a customer who has never placed an order
INSERT INTO customers VALUES (6, 'Frank Nguyen', 'frank@example.com', 'Bristol', 2024);
```

```sql starter
-- List all customers and their orders (including those with no orders)
SELECT customers.name, orders.id AS order_id
FROM customers
```

```sql solution
SELECT customers.name, orders.id AS order_id, orders.status
FROM customers
LEFT JOIN orders ON orders.customer_id = customers.id
ORDER BY customers.name;
```

# Lesson: Subqueries

A **subquery** is a `SELECT` nested inside another query. Use it in a `WHERE` clause to filter with a derived value.

```sql starter
-- Find products that cost more than the average price
SELECT name, price
FROM products
```

```sql solution
SELECT name, price
FROM products
WHERE price > (SELECT AVG(price) FROM products)
ORDER BY price DESC;
```

# Lesson: Multi-table Aggregation

Combine `JOIN` and `GROUP BY` to answer real business questions.

```sql starter
-- Calculate the total value of each order
SELECT orders.id
FROM orders
```

```sql solution
SELECT
  orders.id,
  customers.name,
  SUM(order_items.quantity * order_items.unit_price) AS order_total
FROM orders
INNER JOIN customers   ON orders.customer_id = customers.id
INNER JOIN order_items ON order_items.order_id = orders.id
GROUP BY orders.id, customers.name
ORDER BY order_total DESC;
```

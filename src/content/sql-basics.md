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

```text explanation
`SELECT` is the command that reads data from a database — it never modifies the data. The `*` wildcard means "all columns". `FROM` tells SQL which table to read from. Every SQL statement ends with a semicolon (`;`). This query returns every row and every column in the `customers` table, which is the starting point for almost all SQL work: see what you're dealing with before you filter or aggregate it.
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

```text explanation
`WHERE` is evaluated *before* `SELECT` selects columns — SQL first narrows the rows, then picks the columns. String values in SQL must be wrapped in single quotes (`'London'`), not double quotes. `AND` requires both conditions to be true; `OR` requires at least one. The comparison operators are `=` (equals), `!=` or `<>` (not equal), `<`, `>`, `<=`, `>=`, and `LIKE` for pattern matching (e.g., `WHERE name LIKE 'A%'` matches names starting with A).
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

```text explanation
`ORDER BY` comes after `WHERE` (if present) and sorts the final result. `ASC` (ascending) is the default — cheapest first for numbers, A–Z for text. `DESC` reverses it. You can sort by multiple columns: `ORDER BY city ASC, name ASC` sorts by city first, then alphabetically within each city. Sorting is computed after the data is filtered, so it only affects how rows are *presented*, not which rows are returned.
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

```text explanation
`LIMIT` is always the last clause in a query. Combine it with `ORDER BY` to get a meaningful "top N" result — without `ORDER BY`, the database returns an arbitrary 3 rows. `LIMIT` runs after sorting, so "top 3 most expensive" works exactly as you'd expect. In production databases with millions of rows, `LIMIT` is essential to keep queries fast during exploration; without it, a `SELECT *` on a large table can return gigabytes of data.
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

```text explanation
Aggregate functions collapse many rows into one result. `AS` gives the output column a readable name (called an *alias*). `COUNT(*)` counts all rows including NULLs; `COUNT(column)` counts only non-NULL values in that column. `ROUND(value, digits)` rounds to a given number of decimal places — essential when `AVG` produces a long decimal. Unlike `SELECT` of raw columns, aggregate functions always produce exactly one row per group (or one row total if there's no `GROUP BY`).
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

```text explanation
`GROUP BY` splits the table into buckets — one per unique value of the grouping column — and then applies the aggregate function to each bucket independently. Every column in `SELECT` that isn't an aggregate function *must* appear in `GROUP BY`; otherwise SQL doesn't know which row's value to use. The `ORDER BY` here references the alias `num_customers` defined in `SELECT`, which is legal in SQL because `ORDER BY` runs last. The result has one row per city, not one row per customer.
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

```text explanation
`INNER JOIN` works by finding rows in both tables where the join condition is true — here, where `orders.customer_id` equals `customers.id`. If an order has no matching customer (orphaned data), that order is excluded from the result. The `ON` clause is not a filter like `WHERE`; it defines the *relationship* between tables. Using `table.column` notation (like `orders.id`) avoids ambiguity when both tables have a column with the same name, which is common with `id`.
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

```text explanation
`LEFT JOIN` preserves every row from the *left* table (the one in `FROM`), even when there is no matching row in the right table. Where there is no match, SQL fills the right-table columns with `NULL`. This is how you answer "which customers have never ordered?" — join customers to orders with a `LEFT JOIN`, then add `WHERE orders.id IS NULL` to filter for the NULLs. The setup block added Frank Nguyen, who has no orders, so you'll see him in the results with `NULL` values for `order_id` and `status`.
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

```text explanation
A subquery in parentheses is evaluated first, and its result is substituted into the outer query. Here, `(SELECT AVG(price) FROM products)` runs once, produces a single number (the average), and then the outer query uses that number in its `WHERE` clause. This avoids needing to know the average in advance. Subqueries can also appear in `SELECT` (as a computed column) or `FROM` (as a derived table). When a subquery returns more than one value, use `IN` or `EXISTS` instead of `=` or `>`.
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

```text explanation
This query chains two `INNER JOIN`s to link three tables: `orders` → `customers` (to get the customer name) and `orders` → `order_items` (to get the line items). `SUM(quantity * unit_price)` computes the order total by multiplying quantity by price for each line item, then summing them per order. `GROUP BY orders.id, customers.name` groups all line items for the same order into one row. The SQL standard requires every non-aggregate `SELECT` column to appear in `GROUP BY`, which is why `customers.name` is listed there even though it's functionally determined by `orders.id`.
```

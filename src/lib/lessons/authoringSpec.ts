export const AUTHORING_SPEC = `# Code Lab — Lesson Authoring Format

Paste these instructions into a Claude project to generate course files that import correctly into Code Lab.

## File structure

One \`.md\` file = one course. The file has two parts: YAML frontmatter and lesson sections.

## Frontmatter (required)

\`\`\`yaml
---
course: My Course Title
language: python          # must be exactly "python" or "sql"
description: One-line summary shown in the sidebar
---
\`\`\`

## Lessons

Separate lessons with a top-level heading that starts with exactly \`# Lesson: \`:

\`\`\`
# Lesson: Variables and f-strings
\`\`\`

Each lesson body can contain:
- Free markdown prose (explanations, lists, inline code, subheadings)
- **Named code blocks** with a second token that declares the role

### Named code block roles

| Role | Purpose | Format |
|------|---------|--------|
| \`starter\` | Code pre-loaded in the editor | \`\`\`python starter |
| \`solution\` | Revealed when user clicks "Show solution" | \`\`\`python solution |
| \`expected\` | Expected output shown as target | \`\`\`text expected |
| \`setup\` | SQL only — DDL/DML run before user code | \`\`\`sql setup |

Only blocks with a recognised role are extracted; all others render as normal code blocks in the lesson prose.

## Complete example

\`\`\`markdown
---
course: Python Basics
language: python
description: Learn Python from scratch — variables, loops, functions
---

# Lesson: Variables and f-strings

A **variable** stores a value. Use an f-string to embed variables in text:

\`\`\`python starter
name = "world"
print(name)
\`\`\`

\`\`\`python solution
name = "world"
print(f"Hello, {name}!")
\`\`\`

\`\`\`text expected
Hello, world!
\`\`\`

Change \`name\` to your own name and use an f-string to print a greeting.

# Lesson: For loops

Use \`for\` to iterate over a sequence.

\`\`\`python starter
fruits = ["apple", "banana", "cherry"]
# print each fruit
\`\`\`

\`\`\`python solution
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(fruit)
\`\`\`
\`\`\`

## SQL example with setup

\`\`\`markdown
---
course: SQL Joins
language: sql
description: Master INNER, LEFT and RIGHT joins
---

# Lesson: INNER JOIN

An INNER JOIN returns rows that have matching values in both tables.

\`\`\`sql setup
CREATE TABLE departments (id INTEGER, name TEXT);
INSERT INTO departments VALUES (1, 'Engineering'), (2, 'Marketing');
CREATE TABLE employees (id INTEGER, name TEXT, dept_id INTEGER);
INSERT INTO employees VALUES (1, 'Alice', 1), (2, 'Bob', 2), (3, 'Carol', 1);
\`\`\`

\`\`\`sql starter
-- Join employees with their department
SELECT employees.name, departments.name AS department
FROM employees
\`\`\`

\`\`\`sql solution
SELECT employees.name, departments.name AS department
FROM employees
INNER JOIN departments ON employees.dept_id = departments.id;
\`\`\`
\`\`\`

## Rules

1. \`language\` in frontmatter must match the language used in starter/solution blocks.
2. Every lesson needs at least a \`starter\` block.
3. The \`setup\` role is only meaningful for SQL lessons.
4. Lesson IDs are derived from the title — keep titles unique within a course.
`;

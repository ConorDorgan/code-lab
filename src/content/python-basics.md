---
course: Python Basics
language: python
description: Learn Python from scratch — variables, loops, functions, and more
---

# Lesson: Hello, World

Python is a readable, beginner-friendly language. The simplest Python program prints text to the screen.

`print()` sends output to stdout. Run the starter code, then try changing the message.

```python starter
print("Hello, World!")
```

```python solution
print("Hello, World!")
```

```text expected
Hello, World!
```

# Lesson: Variables and Data Types

A **variable** gives a name to a value. Python figures out the type automatically.

Common types:
- `int` — whole numbers: `42`
- `float` — decimals: `3.14`
- `str` — text: `"hello"`
- `bool` — `True` or `False`

Use `type()` to inspect a value's type.

```python starter
age = 25
height = 1.75
name = "Conor"
is_learning = True

# Print each variable and its type
print(age, type(age))
```

```python solution
age = 25
height = 1.75
name = "Conor"
is_learning = True

print(age, type(age))
print(height, type(height))
print(name, type(name))
print(is_learning, type(is_learning))
```

# Lesson: f-Strings

f-strings let you embed expressions directly in a string. Prefix the string with `f` and wrap expressions in `{}`.

```python starter
name = "world"
print("Hello, " + name + "!")
```

```python solution
name = "world"
print(f"Hello, {name}!")
# You can embed any expression
print(f"2 + 2 = {2 + 2}")
```

```text expected
Hello, world!
2 + 2 = 4
```

# Lesson: Lists

A **list** holds an ordered collection of items. Access items by index (starting at 0). Lists are mutable — you can add, remove, and change items.

```python starter
fruits = ["apple", "banana", "cherry"]

# Print the first item
print(fruits[0])
```

```python solution
fruits = ["apple", "banana", "cherry"]
print(fruits[0])        # first item
print(fruits[-1])       # last item
print(len(fruits))      # number of items

fruits.append("date")
print(fruits)
```

# Lesson: For Loops

Use `for` to iterate over any sequence — a list, a string, or a `range`.

```python starter
fruits = ["apple", "banana", "cherry"]
# Print each fruit on its own line
```

```python solution
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(fruit)

# range gives a sequence of numbers
for i in range(5):
    print(i)
```

```text expected
apple
banana
cherry
0
1
2
3
4
```

# Lesson: If / Elif / Else

Conditionals let your code make decisions.

```python starter
score = 72

# Print "Pass" if score >= 60, otherwise "Fail"
```

```python solution
score = 72

if score >= 90:
    print("Distinction")
elif score >= 60:
    print("Pass")
else:
    print("Fail")
```

```text expected
Pass
```

# Lesson: Functions

A **function** packages reusable logic. Define it with `def`, call it by name.

```python starter
# Define a function that greets a person by name
```

```python solution
def greet(name: str) -> str:
    return f"Hello, {name}!"

print(greet("Conor"))
print(greet("World"))
```

```text expected
Hello, Conor!
Hello, World!
```

# Lesson: Dictionaries

A **dictionary** maps keys to values. Use `{}` or `dict()` to create one.

```python starter
person = {"name": "Alice", "age": 30, "city": "London"}

# Access the name
print(person["name"])
```

```python solution
person = {"name": "Alice", "age": 30, "city": "London"}

print(person["name"])
print(person.get("country", "Unknown"))  # safe default

# Iterate over key-value pairs
for key, value in person.items():
    print(f"{key}: {value}")
```

# Lesson: List Comprehensions

List comprehensions offer a concise way to build lists.

```python starter
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Create a new list of even numbers using a for loop
evens = []
for n in numbers:
    if n % 2 == 0:
        evens.append(n)
print(evens)
```

```python solution
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# List comprehension — same result, one line
evens = [n for n in numbers if n % 2 == 0]
print(evens)

# Squares of odd numbers
odd_squares = [n**2 for n in numbers if n % 2 != 0]
print(odd_squares)
```

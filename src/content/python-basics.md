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

```text explanation
`print()` is a built-in function that writes its arguments to stdout followed by a newline. You call it by writing the function name, then passing the value you want to display in parentheses. String literals (text) must be wrapped in matching quote characters — either single `'` or double `"`.
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

```text explanation
Python uses *dynamic typing* — you never declare a type explicitly; Python infers it from the value you assign. `type()` returns a type object like `<class 'int'>`. Each call to `print()` here passes two arguments separated by a comma; `print` separates them with a space by default. This pattern — store a value, then inspect it with `type()` — is a useful habit when learning what Python expects.
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

```text explanation
An f-string (formatted string literal) is created by placing `f` immediately before the opening quote. Any expression inside `{}` is evaluated at runtime and converted to a string. This is cleaner than concatenation with `+` because you can see the structure of the output directly. You can put any valid Python expression inside `{}` — not just variable names, but arithmetic, function calls, or even conditionals.
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

```text explanation
Lists in Python are zero-indexed, so the first item is at index `0`. Negative indices count from the end: `fruits[-1]` gives the last item without needing to know the length. `len()` returns the number of items. `.append()` adds an item to the end of the list, mutating it in place — the list itself changes rather than a new one being created. This mutability is a key property of lists, distinguishing them from tuples.
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

```text explanation
A `for` loop binds a variable (here `fruit` or `i`) to each item in a sequence in turn, then runs the indented block of code. Python uses indentation (4 spaces by convention) to define blocks — there are no curly braces. `range(5)` produces the sequence `0, 1, 2, 3, 4`; it stops *before* the number you pass in. You can loop over any iterable: lists, strings, tuples, dicts, and more.
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

```text explanation
Python evaluates `if` conditions top to bottom and runs the first block whose condition is `True`. `elif` (short for "else if") checks an additional condition only when all previous conditions were `False`. `else` catches everything that didn't match. Conditions use comparison operators: `>=` (greater than or equal), `==` (equal), `!=` (not equal), `<`, `>`, `<=`. Only one branch ever runs — once a match is found, the rest are skipped.
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

```text explanation
`def` declares a function. The parameter list in parentheses names the inputs. Python supports optional *type hints* (`name: str` and `-> str`) that document what types the function expects and returns — they don't enforce anything at runtime but help you and your editor understand the code. `return` sends a value back to the caller. Once defined, you call the function by its name followed by arguments in parentheses; each call runs the function body independently.
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

```text explanation
Dictionaries store key-value pairs. Access a value with `dict[key]` — if the key doesn't exist this raises a `KeyError`. `.get(key, default)` is safer: it returns the default instead of raising an error. `.items()` returns all key-value pairs as tuples, which you can unpack into two variables in a `for` loop. Dictionary keys must be *hashable* (strings, numbers, and tuples work; lists do not). Since Python 3.7, dictionaries preserve insertion order.
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

```text explanation
A list comprehension packs a `for` loop and optional `if` filter into a single expression: `[expression for item in iterable if condition]`. The result is a new list — the original is not modified. `%` is the modulo operator (remainder after division), so `n % 2 == 0` is `True` for even numbers. `**` is the exponentiation operator (`n**2` means n squared). Comprehensions are idiomatic Python — prefer them over explicit `append` loops for simple transformations and filters.
```

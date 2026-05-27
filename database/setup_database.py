import sqlite3


connection = sqlite3.connect("database/sales_database.db")


cursor = connection.cursor()


# CREATE CUSTOMER TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS customer (
    customer_id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT,
    join_date TEXT
)
""")


# CREATE SALES TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS sales (
    sale_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    product TEXT,
    amount REAL,
    sale_date TEXT,
    FOREIGN KEY(customer_id)
    REFERENCES customer(customer_id)
)
""")


# INSERT SAMPLE CUSTOMER DATA
customers = [
    (1, "Rahul Sharma", "rahul@gmail.com", "2025-01-10"),
    (2, "Priya Verma", "priya@gmail.com", "2025-02-15"),
    (3, "Amit Singh", "amit@gmail.com", "2025-03-01")
]

cursor.executemany("""
INSERT OR REPLACE INTO customer
VALUES (?, ?, ?, ?)
""", customers)


# INSERT SAMPLE SALES DATA
sales = [
    (1, 1, "Laptop", 1200, "2026-05-20"),
    (2, 2, "Phone", 800, "2026-05-22"),
    (3, 1, "Headphones", 150, "2026-05-23"),
    (4, 3, "Tablet", 600, "2026-05-24")
]

cursor.executemany("""
INSERT OR REPLACE INTO sales
VALUES (?, ?, ?, ?, ?)
""", sales)


# Commit changes
connection.commit()

print("Database and tables created successfully!")

connection.close()
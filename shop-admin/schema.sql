CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS brands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL DEFAULT 0,
    description TEXT,
    stock_quantity INT NOT NULL DEFAULT 0,
    category_id INT,
    brand_id INT,
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (brand_id) REFERENCES brands(id)
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number VARCHAR(50) NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    customer_phone VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'new',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

INSERT INTO categories (name) VALUES ('Смартфоны'), ('Ноутбуки'), ('Наушники'), ('Телевизоры');
INSERT INTO brands (name) VALUES ('Apple'), ('Samsung'), ('Xiaomi'), ('Sony'), ('Lenovo');

INSERT INTO products (name, price, description, stock_quantity, category_id, brand_id) VALUES
('iPhone 15', 89990, 'Смартфон Apple, 128 ГБ', 12, 1, 1),
('Galaxy S24', 79990, 'Смартфон Samsung, 256 ГБ', 8, 1, 2),
('Redmi Note 13', 21990, 'Смартфон Xiaomi, 128 ГБ', 25, 1, 3),
('MacBook Air M2', 119990, 'Ноутбук Apple 13 дюймов', 4, 2, 1),
('IdeaPad 5', 64990, 'Ноутбук Lenovo 15.6 дюймов', 6, 2, 5),
('WH-1000XM5', 34990, 'Беспроводные наушники Sony', 10, 3, 4),
('Bravia 55X80L', 99990, 'Телевизор Sony 55 дюймов', 3, 4, 4);

INSERT INTO orders (order_number, customer_name, customer_phone, status, created_at) VALUES
('A-1001', 'Иванов Иван', '+7 900 111-22-33', 'new', '2026-10-15 10:20:00'),
('A-1002', 'Петрова Анна', '+7 900 222-33-44', 'assembling', '2026-10-16 14:05:00'),
('A-1003', 'Сидоров Олег', '+7 900 333-44-55', 'shipped', '2026-10-17 09:40:00'),
('A-1004', 'Кузнецова Мария', '+7 900 444-55-66', 'completed', '2026-10-18 18:15:00');

INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(1, 1, 1, 89990),
(1, 6, 1, 34990),
(2, 3, 2, 21990),
(3, 4, 1, 119990),
(4, 7, 1, 99990),
(4, 6, 2, 34990);

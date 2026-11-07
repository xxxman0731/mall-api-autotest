-- MySQL 版被测库初始化脚本(可选:框架切换 MySQL 模式时使用)
-- 执行方式: mysql -uroot -p < db/mall.sql
CREATE DATABASE IF NOT EXISTS mall DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE mall;

DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS products;

CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(32) NOT NULL UNIQUE,
  password VARCHAR(64) NOT NULL,
  phone VARCHAR(11),
  created_at VARCHAR(32) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  stock INT NOT NULL,
  status INT DEFAULT 1
) ENGINE=InnoDB;

CREATE TABLE orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_no VARCHAR(64) NOT NULL UNIQUE,
  user_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT NOT NULL,
  total_price DECIMAL(10,2) NOT NULL,
  status INT DEFAULT 1,
  created_at VARCHAR(32) NOT NULL
) ENGINE=InnoDB;

INSERT INTO products(name, price, stock, status) VALUES
('iPhone 15 Pro', 8999.00, 100, 1),
('小米手环 9', 249.00, 500, 1),
('罗技鼠标 MX Master 3S', 699.00, 200, 1),
('机械键盘 K870', 399.00, 150, 1),
('显示器 27寸 4K', 1999.00, 80, 1);

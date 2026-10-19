PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS rooms (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    room_number TEXT    NOT NULL,
    floor       INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS employees (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name  TEXT NOT NULL,
    department TEXT,
    position   TEXT
);

CREATE TABLE IF NOT EXISTS equipment (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_number TEXT NOT NULL UNIQUE,
    device_type      TEXT NOT NULL,
    model            TEXT,
    specs            TEXT,
    room_id          INTEGER REFERENCES rooms(id) ON DELETE SET NULL,
    employee_id      INTEGER REFERENCES employees(id) ON DELETE SET NULL,
    ip_address       TEXT,
    status           TEXT NOT NULL DEFAULT 'in_stock'
                      CHECK (status IN ('working', 'in_stock', 'broken', 'decommissioned'))
);

CREATE TABLE IF NOT EXISTS warehouse (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    category      TEXT,
    quantity      INTEGER NOT NULL DEFAULT 0,
    min_threshold INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS repairs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    repair_date  TEXT NOT NULL,
    admin_name   TEXT NOT NULL,
    description  TEXT NOT NULL
);

-- Демо-данные, чтобы при первом запуске сайт не был пустым

INSERT INTO rooms (room_number, floor) VALUES
    ('301', 3),
    ('302', 3),
    ('105', 1),
    ('Склад', 1);

INSERT INTO employees (full_name, department, position) VALUES
    ('Иванов Пётр Сергеевич', 'Бухгалтерия', 'Главный бухгалтер'),
    ('Смирнова Анна Викторовна', 'Отдел продаж', 'Менеджер'),
    ('Кузнецов Олег Дмитриевич', 'Отдел продаж', 'Руководитель отдела'),
    ('Фёдорова Мария Игоревна', 'HR', 'HR-специалист');

INSERT INTO equipment (inventory_number, device_type, model, specs, room_id, employee_id, ip_address, status) VALUES
    ('INV-0001', 'Компьютер', 'Dell OptiPlex 7010', 'Core i5-3470, 8GB RAM, SSD 256GB', 1, 1, '10.0.1.12', 'working'),
    ('INV-0002', 'Монитор', 'Samsung S24D300', '24", Full HD', 1, 1, NULL, 'working'),
    ('INV-0003', 'Компьютер', 'HP ProDesk 600 G3', 'Core i5-7500, 8GB RAM, HDD 500GB', 2, 2, '10.0.1.18', 'broken'),
    ('INV-0004', 'Монитор', 'LG 22MK400H', '22", Full HD', 2, 2, NULL, 'working'),
    ('INV-0005', 'Принтер', 'Canon LBP6030', 'Лазерный, ч/б, A4', 2, NULL, '10.0.1.40', 'working'),
    ('INV-0006', 'Компьютер', 'Lenovo ThinkCentre M720', 'Core i5-9400, 16GB RAM, SSD 512GB', 3, 3, '10.0.1.21', 'working'),
    ('INV-0007', 'Монитор', 'AOC 24B2XH', '24", Full HD, IPS', 3, 3, NULL, 'working'),
    ('INV-0008', 'Компьютер', 'Dell OptiPlex 3020', 'Core i3-4130, 4GB RAM, HDD 500GB', 4, NULL, NULL, 'in_stock'),
    ('INV-0009', 'МФУ', 'Kyocera M2040dn', 'Лазерное, ч/б, сетевое', 1, NULL, '10.0.1.41', 'working'),
    ('INV-0010', 'Компьютер', 'Acer Veriton X2665G', 'Core i5-10400, 8GB RAM, SSD 256GB', 4, NULL, NULL, 'decommissioned'),
    ('INV-0011', 'Монитор', 'Samsung S22F350', '22", Full HD', 4, NULL, NULL, 'broken');

INSERT INTO warehouse (name, category, quantity, min_threshold) VALUES
    ('Картридж HP 05A', 'Картриджи', 2, 3),
    ('Картридж Kyocera TK-1150', 'Картриджи', 5, 2),
    ('Мышь Logitech B100', 'Периферия', 14, 5),
    ('Клавиатура A4Tech KK-3', 'Периферия', 3, 4),
    ('Патч-корд UTP 2м', 'Кабели', 22, 10),
    ('Патч-корд UTP 5м', 'Кабели', 6, 8),
    ('Блок питания 450W', 'Запчасти', 1, 2),
    ('Оперативная память DDR4 8GB', 'Запчасти', 4, 3);

INSERT INTO repairs (equipment_id, repair_date, admin_name, description) VALUES
    (3, '2026-09-02', 'Белов А.С.', 'Диагностика не включается — вышел из строя блок питания, требуется замена'),
    (1, '2026-08-14', 'Белов А.С.', 'Чистка от пыли, замена термопасты'),
    (11, '2026-09-20', 'Белов А.С.', 'Не включается подсветка матрицы, похоже на обрыв шлейфа'),
    (5, '2026-07-30', 'Белов А.С.', 'Замена картриджа, прочистка барабана'),
    (10, '2026-06-01', 'Белов А.С.', 'Списан по акту — материнская плата неремонтопригодна'),
    (1, '2026-05-11', 'Белов А.С.', 'Установка SSD вместо HDD, перенос системы');

import os
import sqlite3

from flask import Flask, render_template, request, redirect, url_for, abort

app = Flask(__name__)

DB_FILE = os.path.join(os.path.dirname(__file__), 'shop.db')

STATUSES = {
    'new': 'Новый',
    'assembling': 'В сборке',
    'shipped': 'Отправлен',
    'completed': 'Завершен',
}


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    if os.path.exists(DB_FILE):
        return
    conn = get_db()
    with open(os.path.join(os.path.dirname(__file__), 'schema.sql'), encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


@app.template_filter('money')
def money(value):
    return '{:,.2f}'.format(float(value or 0)).replace(',', ' ').replace('.', ',') + ' ₽'


@app.template_filter('date')
def format_date(value):
    if not value:
        return ''
    date_part, _, time_part = str(value).partition(' ')
    year, month, day = date_part.split('-')
    return day + '.' + month + '.' + year + ' ' + time_part[:5]


@app.context_processor
def add_statuses():
    return {'statuses': STATUSES}


@app.route('/')
def products():
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', 0, type=int)

    sql = '''SELECT p.*, c.name AS category_name, b.name AS brand_name
             FROM products p
             LEFT JOIN categories c ON c.id = p.category_id
             LEFT JOIN brands b ON b.id = p.brand_id
             WHERE 1 = 1'''
    params = []

    if search:
        sql += ' AND p.name LIKE ?'
        params.append('%' + search + '%')

    if category_id:
        sql += ' AND p.category_id = ?'
        params.append(category_id)

    sql += ' ORDER BY p.name'

    conn = get_db()
    product_list = conn.execute(sql, params).fetchall()
    categories = conn.execute('SELECT * FROM categories ORDER BY name').fetchall()
    conn.close()

    return render_template('products.html', products=product_list, categories=categories,
                           search=search, category_id=category_id, message=request.args.get('message'))


@app.route('/product/add', methods=['GET', 'POST'])
@app.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
def product_form(product_id=None):
    conn = get_db()
    errors = []

    product = {
        'name': '',
        'price': '',
        'description': '',
        'stock_quantity': 0,
        'category_id': 0,
        'brand_id': 0,
    }

    if product_id:
        row = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        if row is None:
            conn.close()
            abort(404)
        product = dict(row)

    if request.method == 'POST':
        product['name'] = request.form.get('name', '').strip()
        product['price'] = request.form.get('price', '').strip().replace(',', '.')
        product['description'] = request.form.get('description', '').strip()
        product['stock_quantity'] = request.form.get('stock_quantity', 0, type=int)
        product['category_id'] = request.form.get('category_id', 0, type=int)
        product['brand_id'] = request.form.get('brand_id', 0, type=int)

        if product['name'] == '':
            errors.append('Введите название товара')

        try:
            price = float(product['price'])
            if price < 0:
                errors.append('Цена не может быть отрицательной')
        except ValueError:
            errors.append('Цена должна быть числом')

        if product['stock_quantity'] is None or product['stock_quantity'] < 0:
            errors.append('Количество должно быть целым числом не меньше нуля')
        if not product['category_id']:
            errors.append('Выберите категорию')
        if not product['brand_id']:
            errors.append('Выберите бренд')

        if not errors:
            data = (product['name'], price, product['description'], product['stock_quantity'],
                    product['category_id'], product['brand_id'])
            if product_id:
                conn.execute('''UPDATE products SET name = ?, price = ?, description = ?,
                                stock_quantity = ?, category_id = ?, brand_id = ?
                                WHERE id = ?''', data + (product_id,))
            else:
                conn.execute('''INSERT INTO products (name, price, description, stock_quantity, category_id, brand_id)
                                VALUES (?, ?, ?, ?, ?, ?)''', data)
            conn.commit()
            conn.close()
            return redirect(url_for('products', message='saved'))

    categories = conn.execute('SELECT * FROM categories ORDER BY name').fetchall()
    brands = conn.execute('SELECT * FROM brands ORDER BY name').fetchall()
    conn.close()

    return render_template('product_form.html', product=product, product_id=product_id,
                           categories=categories, brands=brands, errors=errors)


@app.route('/product/<int:product_id>/delete', methods=['POST'])
def product_delete(product_id):
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM order_items WHERE product_id = ?', (product_id,)).fetchone()[0]
    if count > 0:
        conn.close()
        return redirect(url_for('products', message='error'))

    conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('products', message='deleted'))


@app.route('/orders')
def orders():
    status = request.args.get('status', '')

    conn = get_db()
    if status in STATUSES:
        order_list = conn.execute('SELECT * FROM orders WHERE status = ? ORDER BY created_at DESC', (status,)).fetchall()
    else:
        order_list = conn.execute('SELECT * FROM orders ORDER BY created_at DESC').fetchall()
    conn.close()

    return render_template('orders.html', orders=order_list, filter_status=status,
                           saved=request.args.get('saved'))


@app.route('/order/<int:order_id>/status', methods=['POST'])
def order_status(order_id):
    status = request.form.get('status', '')

    if status in STATUSES:
        conn = get_db()
        conn.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
        conn.commit()
        conn.close()

    if request.form.get('back') == 'order':
        return redirect(url_for('order_view', order_id=order_id, saved=1))
    return redirect(url_for('orders', saved=1))


@app.route('/order/<int:order_id>')
def order_view(order_id):
    conn = get_db()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    if order is None:
        conn.close()
        abort(404)

    items = conn.execute('''SELECT oi.*, p.name AS product_name
                            FROM order_items oi
                            LEFT JOIN products p ON p.id = oi.product_id
                            WHERE oi.order_id = ?''', (order_id,)).fetchall()
    conn.close()

    total = 0
    for item in items:
        total += item['price'] * item['quantity']

    return render_template('order.html', order=order, items=items, total=total,
                           saved=request.args.get('saved'))


@app.route('/directory', methods=['GET', 'POST'])
def directory():
    conn = get_db()
    error = ''

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        item_type = request.form.get('type', '')

        if name == '':
            error = 'Название не может быть пустым'
        elif item_type == 'category':
            conn.execute('INSERT INTO categories (name) VALUES (?)', (name,))
            conn.commit()
            conn.close()
            return redirect(url_for('directory', saved=1))
        elif item_type == 'brand':
            conn.execute('INSERT INTO brands (name) VALUES (?)', (name,))
            conn.commit()
            conn.close()
            return redirect(url_for('directory', saved=1))

    categories = conn.execute('''SELECT c.id, c.name, COUNT(p.id) AS products_count
                                 FROM categories c
                                 LEFT JOIN products p ON p.category_id = c.id
                                 GROUP BY c.id, c.name
                                 ORDER BY c.name''').fetchall()
    brands = conn.execute('''SELECT b.id, b.name, COUNT(p.id) AS products_count
                             FROM brands b
                             LEFT JOIN products p ON p.brand_id = b.id
                             GROUP BY b.id, b.name
                             ORDER BY b.name''').fetchall()
    conn.close()

    return render_template('directory.html', categories=categories, brands=brands,
                           error=error, saved=request.args.get('saved'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)

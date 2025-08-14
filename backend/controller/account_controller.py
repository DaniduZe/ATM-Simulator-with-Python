from flask import Blueprint, request, jsonify
import psycopg2
import psycopg2.extras

account_bp = Blueprint('account', __name__)

DATABASE = {
    'dbname': 'your_db_name',
    'user': 'your_db_user',
    'password': 'your_db_password',
    'host': 'localhost',
    'port': 5432
}

def get_db_connection():
    conn = psycopg2.connect(**DATABASE)
    return conn

@account_bp.route('/create_customer', methods=['POST'])
def create_customer():
    data = request.get_json()
    nic = data.get('nic')
    name = data.get('name')
    pin = data.get('pin')
    dob = data.get('dob')
    mobilenum = data.get('mobilenum')

    if not all([nic, name, pin, dob, mobilenum]):
        return jsonify({'error': 'Missing fields'}), 400

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('SELECT * FROM customers WHERE nic = %s', (nic,))
    existing = cur.fetchone()
    if existing:
        cur.close()
        conn.close()
        return jsonify({'error': 'Customer already exists'}), 409

    cur.execute(
        'INSERT INTO customers (nic, name, pin, dob, mobilenum) VALUES (%s, %s, %s, %s, %s)',
        (nic, name, pin, dob, mobilenum)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Customer created successfully'}), 201

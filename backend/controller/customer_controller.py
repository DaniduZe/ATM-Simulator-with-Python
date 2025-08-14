from db import get_db_connection
from psycopg2 import sql
import re
from datetime import datetime, timedelta
import bcrypt
import jwt
from flask import current_app


# -------------------- NIC Validation --------------------
def validate_sri_lankan_nic(nic: str) -> bool:
    old_pattern = r"^\d{9}[VvXx]$"
    new_pattern = r"^\d{12}$"

    if re.match(old_pattern, nic):
        year_part = int(nic[:2])
        days_part = int(nic[2:5])
        if 1 <= days_part <= 366 or 501 <= days_part <= 866:
            return True
        return False
    elif re.match(new_pattern, nic):
        year_part = int(nic[:4])
        days_part = int(nic[4:7])
        current_year = datetime.now().year
        if not (1900 <= year_part <= current_year):
            return False
        if 1 <= days_part <= 366 or 501 <= days_part <= 866:
            return True
        return False
    else:
        return False


# -------------------- Password Hashing --------------------
def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


# -------------------- Create Customer --------------------
def create_customer(data):
    nic = data.get("nic")
    name = data.get("name")
    pin = data.get("pin")
    dob = data.get("dob")
    mobile_num = data.get("mobilenum")

    if not nic or not name or not pin or not dob or not mobile_num:
        return {"error": "Missing required fields"}, 400

    if not validate_sri_lankan_nic(nic):
        return {"error": "Invalid NIC format"}, 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Check if NIC exists
        cur.execute("SELECT 1 FROM customers WHERE nic = %s", (nic,))
        if cur.fetchone():
            return {"error": "Customer with this NIC already exists"}, 404

        # Generate new ID
        cur.execute("SELECT MAX(id) FROM customers")
        max_id = cur.fetchone()[0]
        new_id = 1000 if max_id is None else max_id + 1

        # Hash PIN
        hashed_pin = hash_password(pin)

        # Insert customer
        insert_query = sql.SQL("""
            INSERT INTO customers (id, nic, name, pin, dob, mobile_num)
            VALUES (%s, %s, %s, %s, %s, %s)
        """)
        cur.execute(insert_query, (new_id, nic, name, hashed_pin, dob, mobile_num))
        conn.commit()

        return {"message": "Customer created successfully", "id": new_id}, 201

    except Exception as e:
        conn.rollback()
        return {"error": str(e)}, 500

    finally:
        cur.close()
        conn.close()


# -------------------- Login Customer --------------------
def login_customer(data):
    customer_id = data.get("id")
    pin = data.get("pin")

    if not customer_id or not pin:
        return {"error": "Missing id or pin"}, 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT id, pin, nic, name FROM customers WHERE id = %s", (customer_id,))
        row = cur.fetchone()
        if not row:
            return {"error": "Invalid credentials"}, 401

        db_id, db_hashed_pin, db_nic, db_name = row
        if not verify_password(pin, db_hashed_pin):
            return {"error": "Invalid credentials"}, 401

        # JWT payload with 1-hour expiration
        payload = {
            "id": db_id,
            "nic": db_nic,
            "name": db_name,
            "exp": datetime.utcnow() + timedelta(minutes=10) 
        }

        secret = current_app.config.get("SECRET_KEY", "default_secret")
        token = jwt.encode(payload, secret, algorithm="HS256")

        return {"token": token}, 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        cur.close()
        conn.close()


def change_pin(data):
    customer_id = data.get("id")
    pin = data.get("pin")
    new_pin = data.get("newpin")

    if not customer_id or not pin or not new_pin:
        return {"error": "Missing id, pin, or newpin"}, 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Fetch current hashed PIN
        cur.execute("SELECT pin FROM customers WHERE id = %s", (customer_id,))
        row = cur.fetchone()
        if not row:
            return {"error": "Customer not found"}, 404

        db_hashed_pin = row[0]
        if not verify_password(pin, db_hashed_pin):
            return {"error": "Current PIN is incorrect"}, 401

        # Hash new PIN
        hashed_new_pin = hash_password(new_pin)

        # Update DB
        cur.execute("UPDATE customers SET pin = %s WHERE id = %s", (hashed_new_pin, customer_id))
        conn.commit()

        return {"message": "PIN changed successfully"}, 200

    except Exception as e:
        conn.rollback()
        return {"error": str(e)}, 500

    finally:
        cur.close()
        conn.close()


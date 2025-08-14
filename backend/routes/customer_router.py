from flask import Blueprint, request, jsonify
from controller.customer_controller import create_customer, login_customer, change_pin

customer_bp = Blueprint("customer_bp", __name__)

# Create customer route
@customer_bp.route("/customer", methods=["POST"])
def add_customer():
    data = request.get_json()
    response, status = create_customer(data)
    return jsonify(response), status

# Login customer route
@customer_bp.route("/customer/login", methods=["POST"])
def customer_login():
    data = request.get_json()
    response, status = login_customer(data)
    return jsonify(response), status


# Change PIN route
@customer_bp.route("/customer/change-pin", methods=["POST"])
def customer_change_pin():
    data = request.get_json()
    response, status = change_pin(data)
    return jsonify(response), status

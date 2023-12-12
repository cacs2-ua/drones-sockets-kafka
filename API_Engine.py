from flask import Flask, jsonify, request
import json
import hashlib
import os

app = Flask(__name__)


def get_next_drone_id():
    with open("drones.json", 'r') as file:
        data = json.load(file)

    if not data["drones"]:
        return 1
    return int(data["drones"][-1]["id"])+1


def hash_password(password, salt_length=16, iterations=100000):

    salt = os.urandom(salt_length)
    salted_password = salt + password.encode('utf-8')
    hashed_password = hashlib.pbkdf2_hmac('sha256', salted_password, salt, iterations)
    return salt.hex() + hashed_password.hex()


@app.route('/dron', methods=['GET'])
def get_data():
    try:
        if request.method == 'GET':
            file = open('drones.json', 'r')
            data = json.load(file)
            file.close()
            response = {
            'data':data["drones"],
            'error': False,
            'message': 'Items Fetched Successfully'
            }
            return jsonify(response), 200
    
    except Exception as e:
        response = {
        'data': None,
        'error': True,
        'message': f'Error Occurred: {e}'
        }
        return jsonify(response), 500


@app.route('/dron', methods=['POST'])
def post_data():
    try:
        if request.method == 'POST':

            data = request.get_json()
            with open("drones.json", 'r') as file:
                bbDD = json.load(file)
                file.close()

            idDron = get_next_drone_id()
            alias = data["alias"]
            token = data["token"]
            token = hash_password(token)
            data = {
                "id": idDron,
                "alias": alias,
                "token": token
            }
            bbDD["drones"].append(data)

            with open("drones.json", 'w') as file:
                json.dump(bbDD, file, indent=4)
            
            response = {
            'data': data,
            'error': False,
            'message': 'Items Posted Successfully'
            }
            return jsonify(response), 201

    except Exception as e:
        response = {
        'data': None,
        'error': True,
        'message': f'Error Occurred: {e}'
        }
        return jsonify(response), 500


@app.route('/mapa', methods=['GET'])
def get_mapa():
    try:
        if request.method == 'GET':
            file = open('drones.json', 'r')
            data = json.load(file)
            file.close()
            response = {
            'data':data["mapa"],
            'error': False,
            'message': 'Items Fetched Successfully'
            }
            return jsonify(response), 200
    
    except Exception as e:
        response = {
        'data': None,
        'error': True,
        'message': f'Error Occurred: {e}'
        }
        return jsonify(response), 500


if __name__ == '__main__':
    app.debug = True
    app.run(host='192.168.1.8')
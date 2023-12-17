from flask import Flask, jsonify, request
import json
import hashlib
import os
import time

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

def verify_password(stored_password, input_password):

    salt = bytes.fromhex(stored_password[:32])
    salted_password = salt + input_password.encode('utf-8')
    hashed_password = hashlib.pbkdf2_hmac('sha256', salted_password, salt, 100000)
    return hashed_password.hex() == stored_password[32:]

@app.route('/data', methods=['GET'])
def get_data():
    try:
        if request.method == 'GET':
            file = open('drones.json', 'r')
            data = json.load(file)
            file.close()
            response = {
            'data':data,
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

@app.route('/dron', methods=['GET'])
def get_dron():
    try:
        if request.method == 'GET':

            with open("drones.json", 'r') as file:
                bbDD = json.load(file)
                file.close()

            message = "Datos obtenidos correctamente"
            response = {
            'data': bbDD["drones"],
            'error': False,
            'message': message
            }
            return jsonify(response), 200
    
    except Exception as e:
        response = {
        'data': None,
        'error': True,
        'message': f'Error ocurrido: {e}'
        }
        return jsonify(response), 500


@app.route('/dron', methods=['POST'])
def post_dron():
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
                "token": token,
                "time": time.time()
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


@app.route('/dron', methods=['DELETE'])
def delete_data():
    try:
        if request.method == 'DELETE':
            with open("drones.json", 'r') as file:
                bbDD = json.load(file)
                file.close()
            bbDD["drones"] = []
            with open("drones.json", 'w') as file:
                json.dump(bbDD, file, indent=4)

            message = "Datos eliminados correctamente"
            response = {
            'data': bbDD,
            'error': False,
            'message': message
            }
            return jsonify(response), 200
    
    except Exception as e:
        response = {
        'data': None,
        'error': True,
        'message': f'Error ocurrido: {e}'
        }
        return jsonify(response), 500


@app.route('/dron', methods=['PUT'])
def put_dron():
    try:
        if request.method == 'PUT':

            data = request.get_json()
            with open("drones.json", 'r') as file:
                bbDD = json.load(file)
                file.close()

            idDron = data["id"]
            token = data["token"]
            token = hash_password(token)
            for dron in bbDD["drones"]:
                if dron["id"] == idDron:
                    dron["token"] = token
                    dron["time"] = time.time()
                    break

            with open("drones.json", 'w') as file:
                json.dump(bbDD, file, indent=4)
            
            response = {
            'data': data,
            'error': False,
            'message': 'Items Put Successfully'
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
    app.run(host='0.0.0.0')
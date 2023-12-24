import sys
import os
from flask import Flask, jsonify, request
from time import sleep
from termcolor import colored
import socket
import json
import uuid
import pickle
import ssl
import threading
import hashlib
import time

os.system('color')
DATABASE_PATH = "drones.json"
cert = 'certificados/certificadoSockets.pem'

app = Flask(__name__)


def get_next_drone_id():
    try:
        with open("drones.json", 'r') as file:
            data = json.load(file)
            file.close()
    except:
        return get_next_drone_id()

    if not data["drones"]:
        return 1
    return int(data["drones"][-1]["id"])+1


def verify_password(stored_password, input_password):

    salt = bytes.fromhex(stored_password[:32])
    salted_password = salt + input_password.encode('utf-8')
    hashed_password = hashlib.pbkdf2_hmac('sha256', salted_password, salt, 100000)
    return hashed_password.hex() == stored_password[32:]


def hash_password(password, salt_length=16, iterations=100000):

    salt = os.urandom(salt_length)
    salted_password = salt + password.encode('utf-8')
    hashed_password = hashlib.pbkdf2_hmac('sha256', salted_password, salt, iterations)
    return salt.hex() + hashed_password.hex()


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
            password = data["password"]
            token = data["token"]
            password = hash_password(password)
            token = hash_password(token)
            data = {
                "id": idDron,
                "alias": alias,
                "password": password,
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


@app.route('/dron', methods=['PUT'])
def put_dron():
    try:
        if request.method == 'PUT':

            data = request.get_json()
            with open("drones.json", 'r') as file:
                bbDD = json.load(file)
                file.close()

            idDron = data["id"]
            password = data["password"]
            token = data["token"]
            token = hash_password(token)
            for dron in bbDD["drones"]:
                if dron["id"] == idDron:
                    if verify_password(dron["password"], password) == False:
                        response = {
                        'data': data,
                        'error': True,
                        'message': 'Password incorrecto'
                        }
                        return jsonify(response), 501
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


def register_drone(id, alias, password):
    try:
        with open(DATABASE_PATH, 'r') as file:
            data = json.load(file)
            file.close()
    except:
        return register_drone(id, alias, password)

    token = str(uuid.uuid4())
    data["drones"].append({
        "id": id,
        "alias": alias,
        "password": hash_password(password),
        "token": hash_password(token),
        "time": time.time()
    })

    with open(DATABASE_PATH, 'w') as file:
        json.dump(data, file, indent=4)

    return (id,token)


def deal_with_client(connstream):
    respuesta = pickle.loads(connstream.recv(1024))
    if respuesta=="FIN":
        return False
    with connstream:
        alias = respuesta[0]
        password = respuesta[1]
        id = get_next_drone_id()
        send = register_drone(id, alias, password)
        connstream.sendall(pickle.dumps(send))
    return True


def conexion_registry(host,port):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert, cert)

    bindsocket = socket.socket()
    bindsocket.bind((host, port))
    bindsocket.listen(5)
    while(True):
        try:
            newsocket, fromaddr = bindsocket.accept()
            connstream = context.wrap_socket(newsocket, server_side=True)
            print('Conexion recibida')
            try:
                res = deal_with_client(connstream)
                if res == False:
                    connstream.close()
                    return
            finally:
                connstream.close()
        except:
            pass


if __name__ == "__main__":

    # Argumentos de linea de parametros
    if(len(sys.argv))!=2:
        print("\033c")
        sys.exit("\n " + '\x1b[5;30;41m' + " Numero de argumentos incorrecto " + '\x1b[0m' + "\n\n " + colored(">", 'green') + " Uso:  python AD_Registry.py <Puerto Escucha>\n")
    ip_registry,puerto_escucha = sys.argv[1].split(':')
    puerto_escucha=int(puerto_escucha)
    print("\033c")
    con1 = threading.Thread(target=conexion_registry, args=(ip_registry,puerto_escucha, ))
    con1.start()
    app.run(host='0.0.0.0', port=3333, ssl_context=('certificados/certificado_registry2.crt', 'certificados/clave_privada_registry2.pem'))
    con1.join()
    print("\n " + '\x1b[6;30;47m' + " ESPECTACULO FINALIZADO " + '\x1b[0m')
    sys.exit()
    
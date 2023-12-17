from flask import Flask, jsonify, request
import json

app = Flask(__name__)


@app.route('/mapa', methods=['GET'])
def get_mapa():
    try:
        if request.method == 'GET':
            file = open('mapa.json', 'r')
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
    

@app.route('/mapa', methods=['POST'])
def post_mapa():
    try:
        if request.method == 'POST':
            file = open('mapa.json', 'r')
            data = json.load(file)
            file.close()
            data2 = request.get_json()
            data["mapa"] = data2["mapa"]

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
    

@app.route('/mapa', methods=['PUT'])
def put_mapa():
    try:
        if request.method == 'PUT':
            file = open('mapa.json', 'r')
            data = json.load(file)
            file.close()
            data2 = request.get_json()
            pos = data2["pos"]
            data["mapa"][pos[0]][pos[1]] = data2["data"]
            file = open('mapa.json', 'w')
            json.dump(data, file)
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
    

@app.route('/mapa', methods=['DELETE'])
def delete_mapa():
    try:
        if request.method == 'DELETE':
            file = open('mapa.json', 'r')
            data = json.load(file)
            file.close()
            data["mapa"] = []
            file = open('mapa.json', 'w')
            json.dump(data, file)
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
    #app.debug = True
    app.run(host='0.0.0.0', ssl_context=('certificados/certificado_registry.crt', 'certificados/clave_privada_registry.pem'))
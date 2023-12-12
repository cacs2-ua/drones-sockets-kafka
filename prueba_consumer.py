import requests
import json
import uuid

ip = "192.168.1.8"

def get_data():
    try:
        url = 'http://' + ip + ':5000/data'
        response= requests.get(url)
        if response.status_code == 200:
            diccionario_respuesta=response.json()
            print(json.dumps(diccionario_respuesta, indent=4, sort_keys=True), end="\n\n\n\n\n\n")
    except Exception as e:

        response = {
        'data': None,
        'error' : False,
        'message': f'Error Ocurred: {e}'
        }
        print(json.dumps(response, indent=4, sort_keys=True), end="\n\n\n\n\n\n")


def checkDron(idDron, token):
    try:
        url = 'http://' + ip + ':5000/dron'
        data = {
            "id": idDron,
            "alias": "alias",
            "token": token
        }
        response = requests.get(url, json=data)
        diccionario_respuesta = response.json()

        if diccionario_respuesta["error"] == False:
            return diccionario_respuesta["correct"]

    except Exception as e:
        response={
        'data': None,
        'error' : False,
        'message': f'Error Ocurred: {e}'
        }
        print(json.dumps(response, indent=4, sort_keys=True), end="\n\n")


def post_data(token):
    try:
        url = 'http://' + ip + ':5000/dron'
        data = {
            "alias": "alias",
            "token": token
        }
        response = requests.post(url, json=data)
        
        if response.status_code == 201:
            diccionario_respuesta = response.json()
            if diccionario_respuesta["error"] == False:
                return diccionario_respuesta["data"]["id"]

    except Exception as e:
        response={
        'data': None,
        'error' : False,
        'message': f'Error Ocurred: {e}'
        }
        print(json.dumps(response, indent=4, sort_keys=True), end="\n\n")

if __name__ == "__main__":

    token = str(uuid.uuid4())
    
    idDron = post_data(token)
    
    if(checkDron(idDron,token)):
        print("El dron existe")
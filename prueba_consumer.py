import requests
import json
import uuid
from time import sleep

ip = "172.27.218.166"

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
        'error' : True,
        'message': f'Error Ocurred: {e}'
        }
        print(json.dumps(response, indent=4, sort_keys=True), end="\n\n\n\n\n\n")


def checkDron(idDron, token):
    try:
        next = True
        while next:
            next = False
            url = 'http://' + ip + ':5000/dron'
            data = {
                "id": idDron,
                "alias": "alias",
                "token": token
            }
            response = requests.get(url, json=data)
            diccionario_respuesta = response.json()

            print(diccionario_respuesta["message"])
            if diccionario_respuesta["error"] == False and diccionario_respuesta["correct"] == True:
                return True, token
            else:
                if diccionario_respuesta["repeat"] == True:
                    next = True
                    sleep(3)
                    token = str(uuid.uuid4())
                    data = {
                        "id": idDron,
                        "token": token
                    }
                    response = requests.put(url, json=data)
                    if response.status_code != 200 or response.json()["error"] == True:
                        return False, token
                else:
                    return False, token

    except Exception as e:
        response={
        'data': None,
        'error' : True,
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
        'error' : True,
        'message': f'Error Ocurred: {e}'
        }
        print(json.dumps(response, indent=4, sort_keys=True), end="\n\n")
        return False, token

if __name__ == "__main__":

    token = str(uuid.uuid4())
    
    idDron = post_data(token)
    #sleep(20)
    result, token = checkDron(idDron, token)
    if result:
        print("Continuamos")
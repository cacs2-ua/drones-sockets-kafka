import requests
import json
import uuid

ip = "172.21.242.131"

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


def post_data():
    try:
        url = 'http://' + ip + ':5000/dron'
        data = {
            "alias": "alias",
            "token": "contraseña"
        }
        response = requests.post(url, json=data)
        if response.status_code == 201:
            diccionario_respuesta = response.json()
            print(json.dumps(diccionario_respuesta, indent=4, sort_keys=True), end="\n\n\n\n\n\n")

    except Exception as e:
        response={
        'data': None,
        'error' : False,
        'message': f'Error Ocurred: {e}'
        }
        print(json.dumps(response, indent=4, sort_keys=True), end="\n\n\n\n\n\n")

if __name__ == "__main__":
    
    #get_data()
    post_data()
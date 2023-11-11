import sys
import os
from time import sleep
from termcolor import colored
import socket
import json
import uuid

os.system('color')

HOST = '127.0.0.1'
PORT = 65432
DATABASE_PATH = "drones.json"


def register_drone(id, alias):
    with open(DATABASE_PATH, 'r') as file:
        data = json.load(file)

    for drone in data["drones"]:
        if drone["id"] == id:
            return "Dron ya registrado"

    token = str(uuid.uuid4())
    data["drones"].append({
        "id": id,
        "alias": alias,
        "token": token
    })

    with open(DATABASE_PATH, 'w') as file:
        json.dump(data, file, indent=4)

    return (id,token)


def get_next_drone_id():
    with open(DATABASE_PATH, 'r') as file:
        data = json.load(file)

    if not data["drones"]:
        return 1
    return int(data["drones"][-1]["id"])+1


def conexion_registry(host,port):
    while(True):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            s.listen()
            print(f"Escuchando en {host}:{port}")
            conn, addr = s.accept()
            with conn:
                print(f"Conexión desde {addr}")
                data = conn.recv(1024).decode("utf-8")
                alias = data
                id = get_next_drone_id()
                send = register_drone(id, alias)
                conn.sendall(send.encode("utf-8"))


if __name__ == "__main__":

    # Argumentos de linea de parametros
    if(len(sys.argv))!=2:
        print("\033c")
        sys.exit("\n " + '\x1b[5;30;41m' + " Numero de argumentos incorrecto " + '\x1b[0m' + "\n\n " + colored(">", 'green') + " Uso:  python AD_Registry.py <Puerto Escucha>\n")
    ip_registry,puerto_escucha = sys.argv[1].split(':')
    puerto_escucha=int(puerto_escucha)
    conexion_registry(ip_registry,puerto_escucha)
    

import sys
import os
from time import sleep
from termcolor import colored
import socket
import json
import uuid
import pickle
import ssl

os.system('color')
DATABASE_PATH = "drones.json"
cert = 'certServ.pem'


def register_drone(id, alias):
    try:
        with open(DATABASE_PATH, 'r') as file:
            data = json.load(file)
            file.close()
    except:
        return register_drone(id, alias)

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
    try:
        with open(DATABASE_PATH, 'r') as file:
            data = json.load(file)
            file.close()
    except:
        return get_next_drone_id()

    if not data["drones"]:
        return 1
    return int(data["drones"][-1]["id"])+1


def deal_with_client(connstream):
    respuesta = connstream.recv(1024).decode('utf-8')
    if respuesta=="FIN":
        return False
    with connstream:
        alias = respuesta
        id = get_next_drone_id()
        send = register_drone(id, alias)
        connstream.sendall(pickle.dumps(send))
    return True


def conexion_registry(host,port):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert, cert)

    bindsocket = socket.socket()
    bindsocket.bind((host, port))
    bindsocket.listen(5)
    while(True):
        '''
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            s.listen()
            print(f" Escuchando en {host}:{port}")
            conn, addr = s.accept()
            respuesta = conn.recv(1024).decode('utf-8')
            if respuesta=="FIN":
                break
            with conn:
                print(f" Conexión desde {addr}")
                alias = respuesta
                id = get_next_drone_id()
                send = register_drone(id, alias)
                conn.sendall(pickle.dumps(send))
        '''
        
        newsocket, fromaddr = bindsocket.accept()
        connstream = context.wrap_socket(newsocket, server_side=True)
        print('Conexion recibida')
        try:
            res = deal_with_client(connstream)
            if res == False:
                break
        finally:
            connstream.close()


if __name__ == "__main__":

    # Argumentos de linea de parametros
    if(len(sys.argv))!=2:
        print("\033c")
        sys.exit("\n " + '\x1b[5;30;41m' + " Numero de argumentos incorrecto " + '\x1b[0m' + "\n\n " + colored(">", 'green') + " Uso:  python AD_Registry.py <Puerto Escucha>\n")
    ip_registry,puerto_escucha = sys.argv[1].split(':')
    puerto_escucha=int(puerto_escucha)
    print("\033c")
    conexion_registry(ip_registry,puerto_escucha)
    print("\n " + '\x1b[6;30;47m' + " ESPECTACULO FINALIZADO " + '\x1b[0m')
    
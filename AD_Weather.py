import sys
import os
from time import sleep
from termcolor import colored
import socket
import json

os.system('color')


def get_temperature_from_file():
    with open('weather_bd.json', 'r') as file:
        data = json.load(file)
        return data.get("Temperatura")


def start_server(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(1)
    print(f"Escuchando en {host}:{port}...")

    while True:
        conn, addr = s.accept()
        respuesta=conn.recv(1024).decode('utf-8')
        if respuesta == "FIN":
            break
        
        temperature = get_temperature_from_file()
        print(f"Conexion con Engine desde: {addr}\nTemperatura actual: {temperature}°C", end="\n\n")
        
        if temperature is not None:
            conn.send(str(temperature).encode('utf-8'))
        else:
            conn.send("Informacion de temperatura no accesible".encode('utf-8'))
        conn.close()

# Parte principal del programa
if __name__ == "__main__":
    # Argumentos de linea de parametros
    if(len(sys.argv))!=2:
        print("\033c")
        sys.exit("\n " + '\x1b[5;30;41m' + " Numero de argumentos incorrecto " + '\x1b[0m' + "\n\n " + colored(">", 'green') + " Uso:  python AD_Weather.py <Puerto Escucha>")
    ip_engine,puerto_engine=sys.argv[1].split(':')
    puerto_engine=int(puerto_engine)

    start_server(ip_engine, puerto_engine)
    print("\n" + '\x1b[6;30;47m' + " ESPECTACULO FINALIZADO " + '\x1b[0m')

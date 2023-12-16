import requests
import json
from termcolor import colored
import sys
import os
import time
from time import sleep

os.system('color')

ip = '192.168.221.160'

def mostrarMapa(mapa):
    print("\033c")
    for i in range (0, 21):
        if i == 0:
            print("      ", end = "")
        else:
            if i < 10:
                print("  " + str(i), end = "  ")
            else:
                print(" " + str(i), end = "  ")
        for j in range (0, 21):
            if j > 0:
                if i == 0:
                    if j < 10:
                        print(" " + str(j), end = "   ")
                    else:
                        print(str(j), end = "   ")
                else:
                    if mapa[j-1][i-1][1]!=True:
                        color = '\x1b[5;30;41m'
                    else:
                        color = '\x1b[6;30;42m'
                    if mapa[j-1][i-1][0]==0:
                        print("    ", end = " ")
                    elif mapa[j-1][i-1][0]<10:
                        print(color + "  " + str(mapa[j-1][i-1][0]) + " " + '\x1b[0m', end = " ")
                    else:
                        print(color + " " + str(mapa[j-1][i-1][0]) + " " + '\x1b[0m', end = " ")
        print("\n")

if __name__ == '__main__':
    while True:
        try:
            url = 'http://' + ip + ':5000/mapa'
            response= requests.get(url)
            if response.status_code == 200:
                diccionario_respuesta=response.json()
                mostrarMapa(diccionario_respuesta['data'])
            sleep(1)

        except Exception as e:
            response = {
            'data': None,
            'error' : False,
            'message': f'Error Ocurred: {e}'
            }
            print(json.dumps(response, indent=4, sort_keys=True), end="\n\n")
            sleep(1)
        

import sys
import os
import time
from time import sleep
from termcolor import colored
import json
from json import loads
from kafka import KafkaConsumer
from kafka import KafkaProducer
from kafka import TopicPartition
import socket
import threading
import pickle

os.system('color')
end = False
start = False
id = 0
bbDD = []


def is_token_valid(token):
    with open('drones.json', 'r') as file:
        data = json.load(file)
        for drone in data["drones"]:
            if drone["token"] == token:
                return True
    return False


def getId(token):
    with open('drones.json', 'r') as file:
        data = json.load(file)
        for drone in data["drones"]:
            if drone["token"] == token:
                return int(drone["id"])
    return None


def listen_for_drones(port,stop_event):
    global start
    global bbDD
    global id
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', port))
        s.listen()
        while True:
            if stop_event.is_set():
                break
            conn, addr = s.accept()
            with conn:
                print(f"Connection from {addr}")
                token = conn.recv(1024).decode('utf-8')
                if is_token_valid(token):
                    id = getId(token)
                    data = ('TOKEN VALIDO',id)
                    conn.sendall(pickle.dumps(data))
                    sleep(1.5)
                    start = True
                    producer3 = KafkaProducer(bootstrap_servers=[puerto_colas],
                        value_serializer=lambda x: 
                        json.dumps(x).encode('utf-8'))
                    data = {"destino" : bbDD}
                    producer3.send('destinos', value=data)
                    producer3.flush()
                else:
                    data = ('TOKEN INVALIDO',0)
                    conn.sendall(pickle.dumps(data))


def get_temperature_from_weather_server(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
        mensaje="OK"
        s.sendall(mensaje.encode('utf-8'))
        temperature_data = s.recv(1024).decode('utf-8')
        s.close()
        try:
            return int(temperature_data)
        except ValueError:
            print(temperature_data)
            return None
    except ConnectionRefusedError:
        return None


def get_temperature_while(ip_weather, puerto_weather,stop_event):
    while True:
        if stop_event.is_set():
            break
        temperature = get_temperature_from_weather_server(ip_weather, puerto_weather)
        if temperature is not None:
            if temperature < 0:
                print("CONDICIONES CLIMATICAS ADVERSAS. ESPECTACULO FINALIZADO.")
        sleep(3)


def recalcularMapa(mapa,newPos,id):
    newS = False
    for i in range (0, 20):
        for j in range (0, 20):
            if mapa[i][j][0]==id:
                newS = mapa[i][j][1]
                mapa[i][j] = (0,False)
    mapa[newPos[0]][newPos[1]]=(id,newS)
    return mapa


def comprobarMapa(mapa):
    for i in range (0, 20):
        for j in range (0, 20):
            if mapa[i][j][0]!=0 and mapa[i][j][1]==False:
                return False
    return True


def mostrarMapa(mapa,completo):
    print("\033c")
    if(comprobarMapa(mapa)):
        print("  " + '\x1b[6;30;47m' + " MAPA DEL ESPECTACULO " + '\x1b[0m', end="                 ")
        if completo==True:
            print("  " + '\x1b[6;30;42m' + " ESPECTACULO FINALIZADO " + '\x1b[0m' + "\n")
        else:
            print("  " + '\x1b[6;30;42m' + " ¡FIGURA COMPLETADA! " + '\x1b[0m' + "\n")
    else:
        print("  " + '\x1b[6;30;47m' + " MAPA DEL ESPECTACULO " + '\x1b[0m' + "\n")
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


def comenzarEspectaculo(puerto_colas,mapa,bbDD,last,first):
    end = False
    stop = False

    producer = KafkaProducer(bootstrap_servers=[puerto_colas],
                         value_serializer=lambda x: 
                         json.dumps(x).encode('utf-8'))
    
    producer2 = KafkaProducer(bootstrap_servers=[puerto_colas],
                         value_serializer=lambda x: 
                         json.dumps(x).encode('utf-8'))
    
    consumer = KafkaConsumer(
        bootstrap_servers=[puerto_colas],
        auto_offset_reset='latest',
        enable_auto_commit=True,
        group_id='drone',
        value_deserializer=lambda x: loads(x.decode('utf-8')))
    goTo = TopicPartition('movimientos', 0)
    consumer.assign([goTo])
    consumer.seek_to_end(goTo)

    data = {"destino" : bbDD}
    producer.send('destinos', value=data)
    producer.flush()
    
    if first:
        for i in range (0, 20):
            mapa.append([])
            for j in range (0, 20):
                if i==0 and j==0:
                    for a in bbDD:
                        if a[0]==id:
                            if a[1][0]==0 and a[1][1]==0:
                                mapa[i].append((id,True))
                            else:
                                mapa[i].append((id,False))
                            break
                else:
                    mapa[i].append((0,False))
        mostrarMapa(mapa,False)

    data2 = {"mapa" : mapa, "completo" : False}
    producer2.send('posiciones', value=data2)
    producer2.flush()

    while end!=True:
        for mensaje in consumer:
            aux = mensaje.value
            mapa = recalcularMapa(mapa,aux["posicion"],aux["id"])

            destino = (0,0)
            for a in bbDD:
                if a[0]==aux["id"]:
                    destino = a[1]
                    break
            if aux["posicion"][0]==destino[0] and aux["posicion"][1]==destino[1]:
                if last:
                    data = {"destino" : ["Stop",aux["id"]]}
                else:
                    data = {"destino" : ["Wait",aux["id"]]}
                new = (mapa[destino[0]][destino[1]][0],True)
                mapa[destino[0]][destino[1]] = new
            else:
                data = {"destino" : bbDD}
            producer.send('destinos', value=data)
            producer.flush()

            mapa = recalcularMapa(mapa,aux["posicion"],aux["id"])

            end = True
            if last:
                for i in range (0, 20):
                    for j in range (0, 20):
                        if (i!=0 or j!=0) and mapa[i][j][0]!=0:
                            end = False
                            break
            else:
                for pos in bbDD:
                    if mapa[pos[1][0]][pos[1][1]][1]==False:
                        end = False
                        break
            mostrarMapa(mapa,(end and last))
            data2 = {"mapa" : mapa, "completo" : end and last}
            producer2.send('posiciones', value=data2)
            producer2.flush()
            break
    return mapa


def conexionWeatherDrone(puerto_escucha, drones, puerto_colas, ip_weather, puerto_weather, stop_event_drone,stop_event_weather):
        # Crear y empezar el hilo para escuchar a los drones
        drone_thread = threading.Thread(target=listen_for_drones, args=(puerto_escucha,stop_event_drone))
        drone_thread.start()
        
        # Crear y empezar el hilo para obtener la temperatura desde AD_Weather
        weather_thread = threading.Thread(target=get_temperature_while, args=(ip_weather, puerto_weather,stop_event_weather))
        weather_thread.start()
        return


def sendNumberOfDrones(host, port,numberOfDrones):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(1)
    print("The number of drones is: " + str(numberOfDrones))
    print(f"Sending the number of drones via the connection {host}:{port}...")
    conn, addr = s.accept()
    print(f"Connection from {addr}")
    bytes_to_send = str(numberOfDrones).encode('utf-8')
    conn.send(bytes_to_send)
    conn.close()


def mainSendNumberOfDrones(host, port,numberOfDrones):
    sendNumberOfDrones(host, port,numberOfDrones)


def finWeather(engine_ip,engine_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((engine_ip, engine_port))
        mensaje="FIN"
        s.sendall(mensaje.encode('utf-8'))

# Parte principal del programa
if __name__ == "__main__":
    # Argumentos de linea de parametros
    if(len(sys.argv))!=5:
        print("\033c")
        sys.exit("\n " + '\x1b[5;30;41m' + " Numero de argumentos incorrecto " + '\x1b[0m' + "\n\n " + colored(">", 'green') + " Uso:  python AD_Engine.py <Puerto Escucha> <Numero Drones> <IP:Puerto Colas> <IP:Puerto Weather>")
    
    ip_AD_Drone, puesto_escucha = sys.argv[1].split(':')
    puesto_escucha=int(puesto_escucha)
    drones = int(sys.argv[2])
    puerto_colas = sys.argv[3]
    ip_weather, puerto_weather = sys.argv[4].split(':')
    puerto_weather = int(puerto_weather)
    
    stop_event_drone = threading.Event()
    stop_event_weather = threading.Event()

    print("\033c")
    print("\n Buscando figuras...")
    while True:
        try:
            file = open('figuras.json', "r+")
            print("\n " + '\x1b[6;30;42m' + " ¡Figuras encontradas! " + '\x1b[0m' + "\n")
            break
        except IOError:
            sleep(0.5)
    try:
        figuras = json.load(file)
    except ValueError:
        print('\x1b[5;30;41m' + " Error en el formato del archivo de figuras " + '\x1b[0m')
        sys.exit()
    file.close()

    conexionWeatherDrone(puesto_escucha, drones, puerto_colas, ip_weather, puerto_weather,stop_event_drone,stop_event_weather)

    #try:
    while True:
        if start:
            break
    count = 0
    mapa = []
    iter = None
    while True:
        if count > 0:
            sleep(1)
            file = open('figuras.json', "r+")
            try:
                figuras = json.load(file)
            except ValueError:
                print('\x1b[5;30;41m' + " Error en el formato del archivo de figuras " + '\x1b[0m')
                sys.exit()
            file.close()
        if count == len(figuras["figuras"]):
            bbDD = []
            for i in iter:
                bbDD.append((i["ID"],(0,0)))
            for i in range (0, 20):
                for j in range (0, 20):
                    if mapa[i][j][0]!=0:
                        mapa[i][j] = (mapa[i][j][0],False)
            mapa = comenzarEspectaculo(puerto_colas,mapa,bbDD,True,False)
            break
        else:
            count2 = 0
            for f in figuras["figuras"]:
                if count2 < count:
                    count2 += 1
                    continue
                count += 1
                count2 += 1
                iter = f["Drones"]
                bbDD = []
                for i in iter:
                    coords = i["POS"].split(",")
                    bbDD.append((i["ID"],(int(coords[0]),int(coords[1]))))
                if count == 1:
                    mapa = comenzarEspectaculo(puerto_colas,mapa,bbDD,False,True)
                else:
                    sleep(5)
                    for i in range (0, 20):
                        for j in range (0, 20):
                            if mapa[i][j][0]!=0:
                                mapa[i][j] = (mapa[i][j][0],False)
                    mapa = comenzarEspectaculo(puerto_colas,mapa,bbDD,False,False)

    stop_event_drone.set()
    stop_event_weather.set()
    finWeather(ip_weather,puerto_weather)
    sleep(3)
    print("\n" + '\x1b[6;30;47m' + " ESPECTÁCULO FINALIZADO " + '\x1b[0m')
    sys.exit()
    '''
    except:
        print("\n " + '\x1b[5;30;41m' + " La comunicacion por Kafka ha fallado " + '\x1b[0m' + "\n")
        sys.exit()
    '''
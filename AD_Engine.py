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
stop = False
id = 0
bbDD = []
conexiones = []
mapa = []


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


def listen_for_drones(port,stop_event,numDrones):
    global start
    global bbDD
    global id
    global stop
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', port))
        s.listen()
        count = 0
        while True:
            if stop_event.is_set() or stop:
                break
            conn, addr = s.accept()
            with conn:
                token = conn.recv(1024).decode('utf-8')
                if is_token_valid(token) and count<numDrones:
                    count += 1
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
        return


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


def finalizarEspectaculo():
    global bbDD
    global mapa
    global conexiones
    global stop
    i = 0
    for a in bbDD:
        bbDD[i] = (a[0],(0,0))
        i += 1
    for i in range (0, 20):
        for j in range (0, 20):
            if mapa[i][j][0]!=0:
                mapa[i][j] = (mapa[i][j][0],False)
    stop = False
    comp = threading.Thread(target=comprobarConexiones, args=(stop_event_conexion, ))
    comp.start()
    mapa = comenzarEspectaculo(puerto_colas,bbDD,True,False)
    stop_event_conexion.set()
    conexiones = []
    stop = True
    return


def get_temperature_while(ip_weather, puerto_weather,stop_event):
    global stop
    global start
    while True:
        if stop_event.is_set() or stop:
            break
        temperature = get_temperature_from_weather_server(ip_weather, puerto_weather)
        if temperature is not None:
            if temperature < 0:
                stop = True
                if start:
                    sleep(10)
                else:
                    sleep(3)
                if bbDD!=[] and start:
                    finalizarEspectaculo()
                print("\n " + '\x1b[5;30;41m' + " CONDICIONES CLIMATICAS ADVERSAS. ESPECTACULO FINALIZADO. " + '\x1b[0m' + "\n")
                break
        sleep(3)
    return


def comprobarConexiones(stop_event):
    global conexiones
    global mapa
    global stop

    while True:
        if stop_event.is_set() or stop:
            break
        change = False
        timeNow = time.time()
        con = conexiones.copy()
        for i in range (0, len(con)):
            if (timeNow-con[i][1])>3:
                for j in range (0, 20):
                    for k in range (0, 20):
                        if mapa[j][k][0]==con[i][0]:
                            mapa[j][k] = (0,False)
                            change = True
        if change:
            producer2 = KafkaProducer(bootstrap_servers=[puerto_colas],
                         value_serializer=lambda x: 
                         json.dumps(x).encode('utf-8'))
            data2 = {"mapa" : mapa, "completo" : False, "cancel" : stop}
            producer2.send('posiciones', value=data2)
            producer2.flush()
            mostrarMapa(False)
    return


def actualizarConexion(id):
    global conexiones
    global mapa
    timeNow = time.time()
    inConexiones = False
    for i in range (0, len(conexiones)):
        if conexiones[i][0]==id:
            inConexiones = True
            conexiones[i] = (id,timeNow)
            break
    if inConexiones==False:
        conexiones.append((id,timeNow))
    
    return


def recalcularMapa(newPos,id):
    global mapa
    newS = False
    for i in range (0, 20):
        for j in range (0, 20):
            if mapa[i][j][0]==id:
                newS = mapa[i][j][1]
                mapa[i][j] = (0,False)
    mapa[newPos[0]][newPos[1]]=(id,newS)
    return mapa


def comprobarMapa():
    global mapa
    for i in range (0, 20):
        for j in range (0, 20):
            if mapa[i][j][0]!=0 and mapa[i][j][1]==False:
                return False
    return True


def mostrarMapa(completo):
    global mapa
    print("\033c")
    if(comprobarMapa()):
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


def comenzarEspectaculo(puerto_colas,bbDD,last,first):
    end = False
    global stop
    global conexiones
    global mapa

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

    if stop:
        return mapa

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
        mostrarMapa(False)

    data2 = {"mapa" : mapa, "completo" : False, "cancel" : stop}
    producer2.send('posiciones', value=data2)
    producer2.flush()

    while end!=True:
        if stop:
            return mapa
        for mensaje in consumer:
            if stop:
                return mapa
            aux = mensaje.value
            mapa = recalcularMapa(aux["posicion"],aux["id"])

            actualizarConexion(aux["id"])

            destino = (0,0)
            for a in bbDD:
                if a[0]==aux["id"]:
                    destino = a[1]
                    break
            if aux["posicion"][0]==destino[0] and aux["posicion"][1]==destino[1]:
                for i in range (0, len(conexiones)):
                    if conexiones[i][0]==aux["id"]:
                        conexiones.pop(i)
                        break
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

            mapa = recalcularMapa(aux["posicion"],aux["id"])

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
            mostrarMapa((end and last))
            data2 = {"mapa" : mapa, "completo" : end and last, "cancel" : stop}
            producer2.send('posiciones', value=data2)
            producer2.flush()
            break
    return mapa


def conexionWeatherDrone(puerto_escucha, drones, ip_weather, puerto_weather, stop_event_drone,stop_event_weather):
        # Crear y empezar el hilo para escuchar a los drones
        drone_thread = threading.Thread(target=listen_for_drones, args=(puerto_escucha,stop_event_drone,drones))
        drone_thread.start()
        
        # Crear y empezar el hilo para obtener la temperatura desde AD_Weather
        weather_thread = threading.Thread(target=get_temperature_while, args=(ip_weather, puerto_weather,stop_event_weather))
        weather_thread.start()
        return


def finWeather(engine_ip,engine_port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((engine_ip, engine_port))
            mensaje="FIN"
            s.sendall(mensaje.encode('utf-8'))
    except:
        return

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
    stop_event_conexion = threading.Event()

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

    conexionWeatherDrone(puesto_escucha, drones, ip_weather, puerto_weather,stop_event_drone,stop_event_weather)

    #try:
    while True:
        if start or stop:
            break
    if stop:
        sys.exit()
    count = 0
    iter = None
    while True:
        if count > 0:
            if stop:
                sys.exit()
            sleep(10)
            if stop:
                sys.exit()
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
            comp = threading.Thread(target=comprobarConexiones, args=(stop_event_conexion, ))
            comp.start()
            mapa = comenzarEspectaculo(puerto_colas,bbDD,True,False)
            if stop:
                sys.exit()
            stop_event_conexion.set()
            conexiones = []
            break
        else:
            if stop:
                sys.exit()
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
                    comp = threading.Thread(target=comprobarConexiones, args=(stop_event_conexion, ))
                    comp.start()
                    mapa = comenzarEspectaculo(puerto_colas,bbDD,False,True)
                    if stop:
                        sys.exit()
                    stop_event_conexion.set()
                    conexiones = []
                else:
                    sleep(5)
                    for i in range (0, 20):
                        for j in range (0, 20):
                            if mapa[i][j][0]!=0:
                                mapa[i][j] = (mapa[i][j][0],False)
                    comp = threading.Thread(target=comprobarConexiones, args=(stop_event_conexion, ))
                    comp.start()
                    mapa = comenzarEspectaculo(puerto_colas,bbDD,False,False)
                    if stop:
                        sys.exit()
                    stop_event_conexion.set()
                    conexiones = []

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
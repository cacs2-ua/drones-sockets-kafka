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
import requests
from cryptography.fernet import Fernet
import ssl
import hashlib
from datetime import datetime


# Variables globales
cert = 'certificados/certificadoSockets.pem'
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(cert, cert)
os.system('color')
end = False
start = False
stop = False
cancel = False
id = 0
dronCount = 0
bbDD = []
completed = []
conexiones = []
mapa = []
auditorias = []


def encryptMensaje(mensaje):
    with open("certificados/fernet.key", "rb") as file:
        key = file.read()
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(mensaje)
    #return mensaje


def decryptMensaje(mensaje):
    with open("certificados/fernet.key", "rb") as file:
        key = file.read()
    cipher_suite = Fernet(key)
    return cipher_suite.decrypt(mensaje)
    #return mensaje


def verify_password(stored_password, input_password):

    salt = bytes.fromhex(stored_password[:32])
    salted_password = salt + input_password.encode('utf-8')
    hashed_password = hashlib.pbkdf2_hmac('sha256', salted_password, salt, 100000)
    return hashed_password.hex() == stored_password[32:]


def is_token_valid(token,password):
    with open('drones.json', 'r') as file:
        data = json.load(file)
        for drone in data["drones"]:
            if verify_password(drone["token"], token) and verify_password(drone["password"], password):
                time = drone["time"]
                return True, time
    return False, 0.0


def getId(token):
    with open('drones.json', 'r') as file:
        data = json.load(file)
        for drone in data["drones"]:
            if verify_password(drone["token"], token):
                return int(drone["id"])
    return None


def listen_for_drones(ip,port,stop_event,numDrones):
    first = True
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        bindsocket = socket.socket()
        bindsocket.bind((ip, port))
        bindsocket.listen(5)
        sleep(1)
        while True:
            global start
            global bbDD
            global id
            global stop
            global dronCount
            global auditorias
            if auditorias!=[]:
                while auditorias!=[]:
                    mensaje = auditorias.pop(0)
                    file = open('auditorias.json', 'r')
                    data = json.load(file)
                    file.close()
                    data["auditorias"].append(mensaje)
                    file = open('auditorias.json', 'w')
                    json.dump(data, file, indent=4)
                    file.close()
            if stop_event.is_set() or stop:
                break
            try:
                newsocket, fromaddr = bindsocket.accept()
                connstream = context.wrap_socket(newsocket, server_side=True)
                try:
                    recieve = pickle.loads(connstream.recv(1024))
                    token = recieve[0]
                    password = recieve[1]
                    result, timeDron = is_token_valid(token,password)
                    if result and dronCount<numDrones:
                        timeDron = time.time() - timeDron
                        id = getId(token)
                        if timeDron < 20.0:
                            dronCount += 1
                            with open("certificados/fernet.key", "rb") as file:
                                key = file.read()
                            data = ('TOKEN VALIDO',id, key)
                            connstream.sendall(pickle.dumps(data))
                            auditorias.append({"Hora": datetime.today().strftime('%Y-%m-%d %H:%M:%S'), "IP": fromaddr[0], "Accion": "Autentificacion exitosa", "Descripcion": "Se ha autentificado un dron con id " + str(id) + " y token " + token + " correctamente."})
                            sleep(1)
                            start = True
                            if first!=True:
                                producer3 = KafkaProducer(bootstrap_servers=[puerto_colas],
                                    value_serializer=lambda x: 
                                    encryptMensaje(json.dumps(x).encode('utf-8')))
                                data = {"destino" : bbDD}
                                producer3.send('destinos', value={"message": data})
                                producer3.flush()
                            first = False
                        else:
                            data = ('TOKEN CADUCADO',id)
                            connstream.sendall(pickle.dumps(data))
                            auditorias.append({"Hora": datetime.today().strftime('%Y-%m-%d %H:%M:%S'), "IP": fromaddr[0], "Accion": "Autentificacion fallida (caducado)", "Descripcion": "Se ha intentado autentificar un dron con id " + str(id) + " y token caducado " + token + "."})
                    else:
                        data = ('TOKEN INVALIDO',0)
                        connstream.sendall(pickle.dumps(data))
                        auditorias.append({"Hora": datetime.today().strftime('%Y-%m-%d %H:%M:%S'), "IP": fromaddr[0], "Accion": "Autentificacion fallida (invalido)", "Descripcion": "Se ha intentado autentificar un dron con id " + str(id) + " y token invalido " + token + "."})
                except:
                    pass
                finally:
                    connstream.close()
            except:
                pass
        return


def get_temperature_from_weather_server():
    try:
        file = open('weather_bd.json', 'r')
        data = json.load(file)
        file.close()
        ciudad = data.get("Ciudad")

        file2 = open('openweather.json', 'r')
        data2 = json.load(file2)
        apiKey = data2.get("key")
        file2.close()

        response = requests.get("https://api.openweathermap.org/data/2.5/weather?q=" + ciudad + "&appid=" + apiKey)
        temperature_data = response.json()["main"]["temp"] - 273.15
        try:
            file = open('weather_bd.json', 'w')
            data["Temperatura"] = round(temperature_data,2)
            json.dump(data, file, indent=4)
            file.close()
            return int(temperature_data)
        except ValueError:
            return None
    except:
        return None


def clearMapa():
    mapa = []
    for i in range (0, 20):
        mapa.append([])
        for j in range (0, 20):
            mapa[i].append((0,False))

    with open("mapa.json", 'r') as file:
        data = json.load(file)
        file.close()

    data["mapa"] = mapa

    with open("mapa.json", 'w') as file:
        json.dump(data, file, indent=4)


def finalizarEspectaculo():
    global bbDD
    global mapa
    global conexiones
    global stop
    global completed
    completed = []
    i = 0
    for a in bbDD:
        bbDD[i] = (a[0],(0,0))
        i += 1
    for i in range (0, 20):
        for j in range (0, 20):
            if mapa[i][j][0]!=0:
                mapa[i][j] = (mapa[i][j][0],False)
    stop = False
    comp = threading.Thread(target=comprobarConexiones, args=(stop_event_conexion,bbDD, ))
    comp.start()
    mapa = comenzarEspectaculo(puerto_colas,bbDD,True,False,mapa)
    clearMapa()
    stop_event_conexion.set()
    conexiones = []
    stop = True
    return


def get_temperature_while(stop_event):
    prevTemp = None
    while True:
        global stop
        global start
        global cancel
        global auditorias
        if stop_event.is_set() or stop:
            break
        temperature = get_temperature_from_weather_server()
        if temperature is not None:
            if prevTemp is None:
                prevTemp = temperature
            else:
                if prevTemp != temperature:
                    auditorias.append({"Hora": datetime.today().strftime('%Y-%m-%d %H:%M:%S'), "IP": "www.openweathermap.org", "Accion": "Cambio de temperatura", "Descripcion": "Ha cambiado la temperatura de " + str(prevTemp) + " a " + str(temperature) + "."})
                    prevTemp = temperature
            
            if temperature < 0:
                auditorias.append({"Hora": datetime.today().strftime('%Y-%m-%d %H:%M:%S'), "IP": "www.openweathermap.org", "Accion": "Repliegue de espectaculo", "Descripcion": "Se detendra el espectaculo debido a las condiciones de clima, temperaturas demasiado bajas."})
                sleep(1)
                stop = True
                cancel = True
                if start:
                    sleep(10)
                else:
                    sleep(3)
                if bbDD!=[] and start:
                    finalizarEspectaculo()
                print("\n " + '\x1b[5;30;41m' + " CONDICIONES CLIMATICAS ADVERSAS - ESPECTACULO FINALIZADO " + '\x1b[0m' + "\n")
                break
        else:
            auditorias.append({"Hora": datetime.today().strftime('%Y-%m-%d %H:%M:%S'), "IP": "www.openweathermap.org", "Accion": "Fallo en la temperatura", "Descripcion": "No funciona el servicio de reconocimiento de la temperatura."})
        sleep(3)
    return


def comprobarMapa(mapa):
    for i in range (0, 20):
        for j in range (0, 20):
            if mapa[i][j][0]!=0 and mapa[i][j][1]==False:
                return False
    return True


def mostrarMapa(completo,dest,auxMap):
    global mapa
    global dronCount
    if mapa == []:
        mapaAux = auxMap.copy()
    else:
        mapaAux = mapa.copy()
    print("\033c")
    if(comprobarMapa(mapaAux)):
        print("  " + '\x1b[6;30;47m' + " MAPA DEL ESPECTACULO " + '\x1b[0m', end="                 ")
        if completo==True:
            print("  " + '\x1b[6;30;42m' + " ESPECTACULO FINALIZADO " + '\x1b[0m' + "\n")
        else:
            if dronCount<len(dest):
                print("  " + '\x1b[6;30;47m' + " ESPERANDO DRONES... " + '\x1b[0m' + "\n")
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
                    if mapaAux[j-1][i-1][1]!=True:
                        color = '\x1b[5;30;41m'
                    else:
                        color = '\x1b[6;30;42m'
                    if mapaAux[j-1][i-1][0]==0:
                        print("    ", end = " ")
                    elif mapaAux[j-1][i-1][0]<10:
                        print(color + "  " + str(mapaAux[j-1][i-1][0]) + " " + '\x1b[0m', end = " ")
                    else:
                        print(color + " " + str(mapaAux[j-1][i-1][0]) + " " + '\x1b[0m', end = " ")
        print("\n")


def comprobarConexiones(stop_event,dest):
    while True:
        global dronCount
        global conexiones
        global mapa
        global cancel
        global stop
        global bbDD
        global completed
        '''
        if mapa == []:
            sleep(0.25)
            continue
        count = 0
        auxDest = bbDD.copy()
        if stop_event.is_set() or stop:
            break
        change = False
        timeNow = time.time()
        con = conexiones.copy()

        for i in range (0, len(con)):
            if (timeNow-con[i][1])>7:
                for j in range (0, 20):
                    for k in range (0, 20):
                        if mapa[j][k][0]==con[i][0] and mapa[j][k][1]==False:
                            mapa[j][k] = (0,False)
                            for a in completed:
                                if a[1][0]==j and a[1][1]==k:
                                    mapa[j][k] = (a[0],True)
                                    break
                            count = count + 1
                            change = True
        if change:
            dronCount = dronCount - count
            producer2 = KafkaProducer(bootstrap_servers=[puerto_colas],
                         value_serializer=lambda x: 
                         json.dumps(x).encode('utf-8'))
            data2 = {"mapa" : mapa, "completo" : False, "cancel" : cancel}
            producer2.send('posiciones', value=data2)
            producer2.flush()
        '''

        sleep(0.25)
        
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
    global completed
    newS = False
    for i in range (0, 20):
        for j in range (0, 20):
            if mapa[i][j][0]==id:
                newS = mapa[i][j][1]
                mapa[i][j] = (0,False)
                for a in completed:
                    if a[1][0]==i and a[1][1]==j:
                        mapa[i][j] = (a[0],True)
                        break
    mapa[newPos[0]][newPos[1]]=(id,newS)
    
    with open("mapa.json", 'r') as file:
        data = json.load(file)
        file.close()

    data["mapa"] = mapa

    with open("mapa.json", 'w') as file:
        json.dump(data, file, indent=4)

    return mapa


def comenzarEspectaculo(puerto_colas,bbDD,last,first,auxMap):
    end = False
    global stop
    global conexiones
    global cancel
    global completed

    producer = KafkaProducer(bootstrap_servers=[puerto_colas],
                         value_serializer=lambda x: 
                         encryptMensaje(json.dumps(x).encode('utf-8')))
    
    producer2 = KafkaProducer(bootstrap_servers=[puerto_colas],
                         value_serializer=lambda x: 
                         encryptMensaje(json.dumps(x).encode('utf-8')))
    
    consumer = KafkaConsumer(
        bootstrap_servers=[puerto_colas],
        auto_offset_reset='latest',
        enable_auto_commit=True,
        group_id='drone',
        value_deserializer=lambda x: loads(decryptMensaje(x).decode('utf-8')))
    goTo = TopicPartition('movimientos', 0)
    consumer.assign([goTo])
    consumer.seek_to_end(goTo)

    if stop:
        return auxMap

    data = {"destino" : bbDD}
    producer.send('destinos', value={"message": data})
    producer.flush()
    
    if first:
        clearMapa()
        global id
        for i in range (0, 20):
            auxMap.append([])
            for j in range (0, 20):
                if i==0 and j==0:
                    auxMap[i].append((0,False))
                else:
                    auxMap[i].append((0,False))
        mostrarMapa(False,bbDD,auxMap)

    data2 = {"mapa" : auxMap, "completo" : False, "cancel" : cancel}
    producer2.send('posiciones', value={"message": data2})
    producer2.flush()

    while end!=True:
        if stop:
            return auxMap
        for mensaje in consumer:
            global mapa
            mapa = auxMap
            if stop:
                return mapa
            aux = mensaje.value["message"]
            aux["posicion"] = aux["posicion"]
            aux["id"] = aux["id"]
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
                new = (aux["id"],True)
                completed.append((aux["id"],destino))
                mapa[destino[0]][destino[1]] = new
            else:
                data = {"destino" : bbDD}
            producer.send('destinos', value={"message": data})
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
            mostrarMapa((end and last),bbDD,mapa)
            data2 = {"mapa" : mapa, "completo" : end and last, "cancel" : cancel}
            producer2.send('posiciones', value={"message": data2})
            producer2.flush()
            break
    return mapa


def conexionWeatherDrone(ip_escucha,puerto_escucha, drones, stop_event_drone,stop_event_weather):
        # Crear y empezar el hilo para escuchar a los drones
        drone_thread = threading.Thread(target=listen_for_drones, args=(ip_escucha,puerto_escucha,stop_event_drone,drones))
        drone_thread.start()
        
        # Crear y empezar el hilo para obtener la temperatura desde AD_Weather
        weather_thread = threading.Thread(target=get_temperature_while, args=(stop_event_weather,))
        weather_thread.start()
        return

# Parte principal del programa
if __name__ == "__main__":
    # Argumentos de linea de parametros
    if(len(sys.argv))!=4:
        print("\033c")
        sys.exit("\n " + '\x1b[5;30;41m' + " Numero de argumentos incorrecto " + '\x1b[0m' + "\n\n " + colored(">", 'green') + " Uso:  python AD_Engine.py <Puerto Escucha> <Numero Drones> <IP:Puerto Colas>")
    
    ip_escucha, puerto_escucha = sys.argv[1].split(':')
    puerto_escucha=int(puerto_escucha)
    drones = int(sys.argv[2])
    puerto_colas = sys.argv[3]
    
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

    conexionWeatherDrone(ip_escucha,puerto_escucha, drones, stop_event_drone,stop_event_weather)

    try:
        while True:
            if start or stop:
                break
        if stop:
            stop_event_drone.set()
            stop_event_weather.set()
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
                completed = []
                for i in iter:
                    bbDD.append((i["ID"],(0,0)))
                for i in range (0, 20):
                    for j in range (0, 20):
                        if mapa[i][j][0]!=0:
                            mapa[i][j] = (mapa[i][j][0],False)
                stop_event_conexion = threading.Event()
                comp = threading.Thread(target=comprobarConexiones, args=(stop_event_conexion,bbDD, ))
                comp.start()
                mapa = comenzarEspectaculo(puerto_colas,bbDD,True,False,mapa)
                clearMapa()
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
                    completed = []
                    for i in iter:
                        coords = i["POS"].split(",")
                        bbDD.append((i["ID"],(int(coords[0]),int(coords[1]))))
                    if count == 1:
                        stop_event_conexion = threading.Event()
                        comp = threading.Thread(target=comprobarConexiones, args=(stop_event_conexion,bbDD, ))
                        comp.start()
                        mapa = comenzarEspectaculo(puerto_colas,bbDD,False,True,mapa)
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
                        stop_event_conexion = threading.Event()
                        comp = threading.Thread(target=comprobarConexiones, args=(stop_event_conexion,bbDD, ))
                        comp.start()
                        mapa = comenzarEspectaculo(puerto_colas,bbDD,False,False,mapa)
                        if stop:
                            sys.exit()
                        stop_event_conexion.set()
                        conexiones = []

        stop_event_drone.set()
        stop_event_weather.set()
        sleep(3)
        print("\n" + '\x1b[6;30;47m' + " ESPECTÁCULO FINALIZADO " + '\x1b[0m')
        sys.exit()
    except:
        print("\n " + '\x1b[5;30;41m' + " La comunicacion por Kafka ha fallado " + '\x1b[0m' + "\n")
        sys.exit()

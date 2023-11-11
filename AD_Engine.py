import sys
import os
from time import sleep
from termcolor import colored
import json
from json import loads
from kafka import KafkaConsumer
from kafka import KafkaProducer
from kafka import TopicPartition
import socket
import kafka
import threading 

os.system('color')
end = False

def is_token_valid(token):
    with open('drones.json', 'r') as file:
        data = json.load(file)
        for drone in data["drones"]:
            if drone["token"] == token:
                return True
    return False

def listen_for_drones(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', port))
        s.listen()
        print(f"Listening on port {port}")
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connection from {addr}")
                token = conn.recv(1024).decode('utf-8')
                if is_token_valid(token):
                    conn.sendall(b'TOKEN VALIDO')
                else:
                    conn.sendall(b'TOKEN INVALIDO')

def get_temperature_from_weather_server(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
        temperature_data = s.recv(1024).decode('utf-8')
        s.close()
        try:
            return int(temperature_data)
        except ValueError:
            print(temperature_data)
            return None
    except ConnectionRefusedError:
        #print("No se puede establecer conexión con AD_Weather. Reintentando...")
        return None


def get_temperature_while(ip_weather, puerto_weather):
    while True:
        temperature = get_temperature_from_weather_server(ip_weather, puerto_weather)
        
        if temperature is not None:
            print(f"Current temperature: {temperature}°C")
            if temperature < 0:
                print("CONDICIONES CLIMATICAS ADVERSAS. ESPECTACULO FINALIZADO.")
                #break
        #else:
            #print("Waiting for valid temperature data...")

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

def comenzarEspectaculo(puerto_colas,mapa,bbDD,last,first):
    end = False

    producer = KafkaProducer(bootstrap_servers=[puerto_colas],
                         value_serializer=lambda x: 
                         json.dumps(x).encode('utf-8'))
    
    producer2 = KafkaProducer(bootstrap_servers=[puerto_colas],
                         value_serializer=lambda x: 
                         json.dumps(x).encode('utf-8'))
    
    consumer = KafkaConsumer(
        bootstrap_servers=[puerto_colas],
        api_version=(0,11,5),
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
                        if a[0]==1:
                            if a[1][0]==0 and a[1][1]==0:
                                mapa[i].append((1,True))
                            else:
                                mapa[i].append((1,False))
                            break
                else:
                    mapa[i].append((0,False))

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
            comp = False
            nextIt = True
            if last:
                comp = True
                for pos in bbDD:
                    if mapa[pos[1][0]][pos[1][1]][1]==False:
                        comp = False
                        nextIt = False
                        break
            if nextIt:
                end = True
            data2 = {"mapa" : mapa, "completo" : comp}
            producer2.send('posiciones', value=data2)
            producer2.flush()
            break
        if end == True:
            return mapa
    return mapa

def conexionWeatherDrone(puerto_escucha, drones, puerto_colas, ip_weather, puerto_weather):
    # Crear y empezar el hilo para escuchar a los drones
    drone_thread = threading.Thread(target=listen_for_drones, args=(puerto_escucha,))
    drone_thread.start()
    
    # Crear y empezar el hilo para obtener la temperatura desde AD_Weather
    weather_thread = threading.Thread(target=get_temperature_while, args=(ip_weather, puerto_weather))
    weather_thread.start()

    #drone_thread.join()
    #weather_thread.join()

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


# Parte principal del programa
if __name__ == "__main__":
    # Argumentos de linea de parametros
    if(len(sys.argv))!=5:
        print("\033c")
        sys.exit("\n " + '\x1b[5;30;41m' + " Numero de argumentos incorrecto " + '\x1b[0m' + "\n\n " + colored(">", 'green') + " Uso:  python AD_Engine.py <Puerto Escucha> <Numero Drones> <IP:Puerto Colas> <IP:Puerto Weather>")
    ip_AD_Drone, puesto_escucha = sys.argv[1].split(':') # Convertir a entero
    puesto_escucha=int(puesto_escucha)
    drones = int(sys.argv[2]) # Convertir a entero
    puerto_colas = sys.argv[3]
    ip_weather, puerto_weather = sys.argv[4].split(':') # Separar la IP y el puerto
    puerto_weather = int(puerto_weather) # Convertir a entero
    #sendNumberOfDrones(ip_AD_Drone,puesto_escucha,drones)
    #print ("Numbers of drones sent to AD_Drone")
    #sleep(3)
    # Leer las figuras del JSON
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

    #try:
    count = 0
    mapa = []
    conexionWeatherDrone(puesto_escucha, drones, puerto_colas, ip_weather, puerto_weather)
    for f in figuras["figuras"]:
        count += 1
        iter = f["Drones"]
        bbDD = []
        for i in iter:
            coords = i["POS"].split(",")
            bbDD.append((i["ID"],(int(coords[0]),int(coords[1]))))
        if count == len(figuras["figuras"]):
            for i in range (0, 20):
                for j in range (0, 20):
                    if mapa[i][j][0]!=0:
                        mapa[i][j] = (mapa[i][j][0],False)
            mapa = comenzarEspectaculo(puerto_colas,mapa,bbDD,True,False)
        elif count == 1:
            mapa = comenzarEspectaculo(puerto_colas,mapa,bbDD,True,True)
        else:
            for i in range (0, 20):
                for j in range (0, 20):
                    if mapa[i][j][0]!=0:
                        mapa[i][j] = (mapa[i][j][0],False)
            mapa = comenzarEspectaculo(puerto_colas,mapa,bbDD,False,False)
    '''
    except:
        print("\n " + '\x1b[5;30;41m' + " La comunicacion por Kafka ha fallado " + '\x1b[0m' + "\n")
        sys.exit()
    '''
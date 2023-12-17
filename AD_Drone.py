import sys
import os
from time import sleep
from termcolor import colored
from kafka import TopicPartition
from kafka import KafkaConsumer
from kafka import KafkaProducer
import json
from json import loads
import socket
import threading
import pickle
from cryptography.fernet import Fernet
import ssl
import uuid
import requests
import urllib3

# Variables globales
os.system('color')
id = None
alias : str = ""
password : str = ""
key = None
DATABASE_PATH = "drones.json"
context = ssl._create_unverified_context()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def encryptMensaje(mensaje):
    global key
    if key != None:
        cipher_suite = Fernet(key)
        return cipher_suite.encrypt(mensaje)
    return mensaje


def decryptMensaje(mensaje):
    global key
    if key != None:
        cipher_suite = Fernet(key)
        return cipher_suite.decrypt(mensaje)
    return mensaje


def update_token(idDron, ip_registry, password):
    try:
        url = 'http://' + ip_registry + ':3333/dron'
        token = str(uuid.uuid4())
        data = {
            "id": idDron,
            "password": password,
            "token": token
        }
        response = requests.put(url, json=data)
        if response.status_code != 200 or response.json()["error"] == True:
            return False, token
        
        return True, token
    except:
        return False, token


# Registrar un dron en AD_Registry
def connect_to_registry(alias,host,port,password):
    while True:
        try:
            '''
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                s.sendall(alias.encode("utf-8"))
                ret = s.recv(1024)
                ret = pickle.loads(ret)
            return ret[0], ret[1]
            '''
            with socket.create_connection((host, port)) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    ssock.sendall(pickle.dumps((alias, password)))
                    ret = ssock.recv(1024)
                    ret = pickle.loads(ret)
                    return ret[0], ret[1]

        except:
            print("\n\n" + '\x1b[5;30;41m' + " No se puede establecer conexión con AD_Registry. Reintentando en 5 segundos... " + '\x1b[0m')
            sleep(5)


def post_data(ip,alias,password):
    try:
        token = str(uuid.uuid4())
        url = 'http://' + ip + ':3333/dron'
        data = {
            "alias": alias,
            "password": password,
            "token": token
        }
        response = requests.post(url, json=data)
        
        if response.status_code == 201:
            diccionario_respuesta = response.json()
            if diccionario_respuesta["error"] == False:
                return diccionario_respuesta["data"]["id"], token
            else:
                return None, token
        else:
            return None, token

    except:
        return None, ""


# Registrar un dron en AD_Registry
def registrarDron(host,port):
    global alias
    global id
    global password
    alias = str(input("\n\n " + colored(">", 'green') + " Introduce un alias para el dron: "))
    password = str(input("\n\n " + colored(">", 'green') + " Introduce una contraseña para el dron: "))
    id, token = connect_to_registry(alias,host,port,password)
    file = open(str(id)+'.txt', 'w')
    file.write(str(token))
    file.close()
    print("\033c" + "\n")
    print(" " + '\x1b[6;30;42m' + " Dron \"" + alias + "\" registrado correctamente con ID = " + str(id) + " " + '\x1b[0m' + "\n\n")
    return id, alias

def api_registrar(host):
    global alias
    global id
    global password
    alias = str(input("\n\n " + colored(">", 'green') + " Introduce un alias para el dron: "))
    password = str(input("\n\n " + colored(">", 'green') + " Introduce una contraseña para el dron: "))
    id, token = post_data(host,alias,password)
    if id == None:
        return None, ""
    file = open(str(id)+'.txt', 'w')
    file.write(str(token))
    file.close()
    print("\033c" + "\n")
    print(" " + '\x1b[6;30;42m' + " Dron \"" + alias + "\" registrado correctamente con ID = " + str(id) + " " + '\x1b[0m' + "\n\n")
    return id, alias

# Comprobar conexion con el Engine
def connectionCheck(puerto_colas, idDron):
    return

# Calcular movimiento del dron
def calcularMovimiento(pos, destino):
    if pos[0] < destino[0]:
        if (20-destino[0]+pos[0]) < (destino[0]-pos[0]):
            if pos[0]==0:
                pos = (19, pos[1])
            else:
                pos = ((pos[0]-1), pos[1])
        else:
            pos = ((pos[0]+1), pos[1])
    elif pos[0] > destino[0]:
        if (20-pos[0]+destino[0]) < (pos[0]-destino[0]):
            if pos[0]==19:
                pos = (0, pos[1])
            else:
                pos = ((pos[0]+1), pos[1])
        else:
            pos = ((pos[0]-1), pos[1])
    else:
        pos = (pos[0], pos[1])
    if pos[1] < destino[1]:
        if (20-destino[1]+pos[1]) < (destino[1]-pos[1]):
            if pos[1]==0:
                pos = (pos[0], 19)
            else:
                pos = (pos[0], (pos[1]-1))
        else:
            pos = (pos[0], (pos[1]+1))
    elif pos[1] > destino[1]:
        if (20-pos[1]+destino[1]) < (pos[1]-destino[1]):
            if pos[1]==19:
                pos = (pos[0], 0)
            else:
                pos = (pos[0], (pos[1]+1))
        else:
            pos = (pos[0], (pos[1]-1))
    else:
        pos = (pos[0], pos[1])
    return pos

# Enviar movimiento del dron al Engine
def enviarMovimiento(pos, destino, puerto_colas, idDron):
    try:
        producer = KafkaProducer(bootstrap_servers=[puerto_colas],
                            value_serializer=lambda x: 
                            encryptMensaje(json.dumps(x).encode('utf-8')))

        pos = calcularMovimiento(pos, destino)
        data = {"id": idDron, "posicion": pos}
        producer.send('movimientos', value={"message": data})
        producer.flush()
        return pos

    except:
        raise Exception()

# Obtener posicion a la que se debe mover el dron
def getDestino(puerto_colas, idDron):
    end = False
    first = True
    timeout = False
    pos = (0,0)
    dest = (0,0)
    try:
        consumer2 = KafkaConsumer(
            bootstrap_servers=[puerto_colas],
            consumer_timeout_ms=2000,
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='drones',
            value_deserializer=lambda x: loads(decryptMensaje(x).decode('utf-8')))
        goTo = TopicPartition('destinos', 0)
        consumer2.assign([goTo])
        consumer2.seek_to_end(goTo)

        while end!=True:
            if first==True:
                first = False
            else:
                if timeout:
                    timeout = False
                else:
                    pos = enviarMovimiento(pos, pos, puerto_colas, idDron)
            for mensaje in consumer2:
                aux = mensaje.value["message"]
                aux["destino"] = aux["destino"]
                '''
                if first:
                    con = threading.Thread(target=connectionCheck, args=(puerto_colas, idDron, ))
                    con.start()
                    first = False
                '''
                if aux["destino"][0]=="Stop" and aux["destino"][1]==idDron:
                    end = True
                    timeout = True
                    break
                elif aux["destino"][0]=="Wait" and aux["destino"][1]==idDron:
                    timeout = True
                    sleep(1)
                    break
                dest = (0,0)
                enter = True
                for a in aux["destino"]:
                    if type(a) is not list:
                        enter = False
                        break
                    if a[0]==idDron:
                        dest = a[1]
                        break
                if dest[0]!=pos[0] or dest[1]!=pos[1]:
                    sleep(0.2)
                    if enter:
                        pos = enviarMovimiento(pos, dest, puerto_colas, idDron)
                if end==True:
                    break

    except:
        raise Exception()

def comprobarMapa(mapa):
    for i in range (0, 20):
        for j in range (0, 20):
            if mapa[i][j][0]!=0 and mapa[i][j][1]==False:
                return False
    return True

# Mostrar mapa del espectaculo
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

# Leer y mostrar mapa del espectaculo
def readMap(puerto_colas,idDron):
    end = False
    try:
        consumer = KafkaConsumer(
            bootstrap_servers=[puerto_colas],
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='drones',
            value_deserializer=lambda x: loads(decryptMensaje(x).decode('utf-8')))
        goTo = TopicPartition('posiciones', 0)
        consumer.assign([goTo])
        consumer.seek_to_end(goTo)

        while end!=True:
            for mensaje in consumer:
                aux = mensaje.value["message"]
                aux["mapa"] = aux["mapa"]
                mostrarMapa(aux["mapa"],aux["completo"])
                print(" " + '\x1b[6;30;42m' + " Dron: " + str(idDron) + " " + '\x1b[0m' + "\n")
                if aux["completo"]==True:
                    sleep(1)
                    if aux["cancel"]==True:
                        print(" " + '\x1b[5;30;41m' + " El espectaculo ha sido cancelado. " + '\x1b[0m' + "\n\n")
                    end = True
                    break
    except:
        raise Exception()
    

# Desarrollo del espectaculo de drones
def realizarEspectaculo(puerto_colas, idDron):

    print("\033c")
    print("\n " + '\x1b[6;30;42m' + " ¡Autentificacion exitosa! " + '\x1b[0m' + "\n")
    print(" Esperando a que se unan todos los drones...\n")
    
    try:
        
        map = threading.Thread(target=readMap, args=(puerto_colas, idDron, ))
        destino = threading.Thread(target=getDestino, args=(puerto_colas, idDron, ))
        map.start()
        destino.start()
        map.join()
        destino.join()
    except:
        print("\033c" + "\n")
        print(" " + '\x1b[5;30;41m' + " La comunicacion por Kafka ha fallado " + '\x1b[0m' + "\n")
    return

# Función para enviar token al AD_Engine para autenticación
def authenticate_with_engine(token, engine_ip, engine_port, password):
    try:
        global id
        '''
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((engine_ip, engine_port))
            s.sendall(token.encode("utf-8"))
            response = pickle.loads(s.recv(1024))
            if response[0]=='TOKEN VALIDO':
                id = response[1]
                return True
            else:
                return False
            '''
        with socket.create_connection((engine_ip, engine_port)) as sock:
            with context.wrap_socket(sock, server_hostname=engine_ip) as ssock:
                ssock.sendall(pickle.dumps((token,password)))
                response = pickle.loads(ssock.recv(1024))
                if response[0]=='TOKEN VALIDO':
                    id = response[1]
                    global key
                    key = response[2]
                    return True, "Contraseña y token correctos, uniendo a espectáculo"
                elif response[0]=='TOKEN INVALIDO':
                    return False, "Contraseña o token incorrectos, acceso denegado"
                else:
                    id = response[1]
                    return False, "Token caducado, solicitando nuevo token"

    except:
        return authenticate_with_engine(token, engine_ip, engine_port, password)

# En la función unirseEspectaculo, después de verificar si el token no está vacío
def unirseEspectaculo(id, ip_engine, puerto_engine):
    
    if id == None:
        id = str(input("\n\n " + colored(">", 'green') + " Introduce el ID del dron: "))
    global password
    password = str(input("\n\n " + colored(">", 'green') + " Introduce la contraseña del dron: "))
    try:
        file = open(str(id)+'.txt', 'r')
        token = ""
        token = file.read()
        file.close()
        if token == "":
            return False, "Dron incorrecto, acceso denegado", password
    except:
        return False, "Dron incorrecto, acceso denegado", password
    if password != "":
        response, message = authenticate_with_engine(token, ip_engine, int(puerto_engine),password)
        return response, message, password
    return False, "Contraseña incorrecta, acceso denegado", password


def cerrarEspectaculo(engine_ip,engine_port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as signal_socket:
            signal_socket.connect((engine_ip, engine_port))
    except:
        return


def finRegistry(ip_registry,puerto_registry):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ip_registry, puerto_registry))
        mensaje="FIN"
        s.sendall(mensaje.encode('utf-8'))

def recbeToken(host,port):
     while(True):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            s.listen()

# Parte principal del programa
if __name__ == "__main__":

    # Argumentos de linea de parametros
    if len(sys.argv)==5:
        if sys.argv[4] != "-d":
            print("\n " + '\x1b[5;30;41m' + "ERROR - El quinto argumento, si existe, ha de ser -d " + '\x1b[0m' + "\n\n")
            sys.exit()
        ip_engine,puerto_engine = sys.argv[1].split(':')
        puerto_engine=int(puerto_engine)
        puerto_colas = sys.argv[2]
        ip_registry, puerto_registry = sys.argv[3].split(':')
        puerto_registry=int(puerto_registry)
        with open(DATABASE_PATH, 'r') as file:
            data = json.load(file)
        
        if not data["drones"]:
            #sleep(1)
            alias="d1"
        else:
            #sleep(1)
            alias="d" + str(int(data["drones"][-1]["id"])+1)
        #sleep(2)
        id,token=connect_to_registry(alias,ip_registry,puerto_registry,"pass")
        file = open(str(id)+'.txt', 'w')
        file.write(str(token))
        file.close()
        #sleep(2)
        while True:
            response, message = authenticate_with_engine(token, ip_engine, int(puerto_engine), "pass")
            if response:
                realizarEspectaculo(puerto_colas, id)
                cerrarEspectaculo(ip_engine,puerto_engine)
                try:
                    finRegistry(ip_registry,puerto_registry)
                except:
                    pass
                sys.exit()
            else:
                if message == "Token caducado, solicitando nuevo token":
                    print("\033c")
                    print("\n " + '\x1b[5;30;41m' + " Autentificación fallida - " + message + " " + '\x1b[0m' + "\n\n")
                    sleep(1)
                    resp, token = update_token(id, ip_registry, "pass")
                    if resp:
                        file = open(str(id)+'.txt', 'w')
                        file.write(str(token))
                        file.close()
                    else:
                        print("\033c")
                        print("\n " + '\x1b[5;30;41m' + " Imposible actualizar token " + '\x1b[0m' + "\n\n")
                        sys.exit()
                    continue
            print("\033c")
            print("\n " + '\x1b[5;30;41m' + " Autentificación fallida - " + message + " " + '\x1b[0m' + "\n\n")
            sys.exit()
        


    if len(sys.argv)!=4:
        print("\033c")
        sys.exit("\n " + '\x1b[5;30;41m' + " Numero de argumentos incorrecto " + '\x1b[0m' + "\n\n " + colored(">", 'green') + " Uso:  python AD_Drone.py <IP:Puerto Engine> <IP:Puerto Colas> <IP:Puerto Registry>")

    ip_engine,puerto_engine = sys.argv[1].split(':')
    puerto_engine=int(puerto_engine)
    puerto_colas = sys.argv[2]
    ip_registry, puerto_registry = sys.argv[3].split(':')
    puerto_registry=int(puerto_registry)

    # Seleccion y ejecucion de acciones
    print("\033c")
    check=True
    while(True):
        print(" " + '\x1b[6;30;47m' + " SELECCIONE UNA ACCIÓN " + '\x1b[0m' + "\n")
        print(" " + colored("1.", 'green') + " Registrar dron (Sockets)")
        print(" " + colored("2.", 'green') + " Registrar dron (API)")
        print(" " + colored("3.", 'green') + " Unirse al espectáculo")
        print(" " + colored("4.", 'green') + " Salir")
        opcion = int(input(" " + "\n " + colored(">", 'green') + " Opción: "))
        if opcion == 1:
            id, alias = registrarDron(ip_registry,puerto_registry)
        elif opcion == 2:
            id, alias = api_registrar(ip_registry)
            if id == None:
                print("\033c")
                print("\n " + '\x1b[5;30;41m' + " Imposible registrar dron " + '\x1b[0m' + "\n\n")
                continue
        elif opcion == 3:
            response, message, password = unirseEspectaculo(id, ip_engine,puerto_engine)
            if response:
                realizarEspectaculo(puerto_colas, id)
                cerrarEspectaculo(ip_engine,puerto_engine)
                try:
                    finRegistry(ip_registry,puerto_registry)
                except:
                    pass
                sys.exit()
            else:
                print("\033c")
                print("\n " + '\x1b[5;30;41m' + " Autentificación fallida - " + message + " " + '\x1b[0m' + "\n\n")
                if message == "Token caducado, solicitando nuevo token":
                    sleep(3)
                    try:
                        resp, token = update_token(id, ip_registry,password)
                        if resp:
                            file = open(str(id)+'.txt', 'w')
                            file.write(str(token))
                            file.close()
                            response, message = authenticate_with_engine(token, ip_engine, int(puerto_engine),password)
                            if response:
                                realizarEspectaculo(puerto_colas, id)
                                cerrarEspectaculo(ip_engine,puerto_engine)
                                try:
                                    finRegistry(ip_registry,puerto_registry)
                                except:
                                    pass
                                sys.exit()
                        else:
                            print("\033c")
                            print("\n " + '\x1b[5;30;41m' + " Imposible actualizar token " + '\x1b[0m' + "\n\n")

                    except:
                        print("\033c")
                        print("\n " + '\x1b[5;30;41m' + " Imposible actualizar token " + '\x1b[0m' + "\n\n")
        elif opcion == 4:
            sys.exit()
        else:
            print("\033c")
            print(" " + '\x1b[5;30;41m' + " Opción incorrecta " + '\x1b[0m' + "\n\n")

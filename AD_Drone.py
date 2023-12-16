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
#from cryptography.fernet import Fernet
import ssl
import base64

# Variables globales
os.system('color')
id : int
alias : str = ""
DATABASE_PATH = "drones.json"
context = ssl._create_unverified_context()


def encryptMensaje(mensaje):
    '''
    with open("fernet.key", "rb") as file:
        clave = file.read()
    cipher_suite = Fernet(clave)
    return pickle.loads(cipher_suite.encrypt(pickle.dumps(mensaje)))
    '''
    return mensaje


def decryptMensaje(mensaje):
    '''
    with open("fernet.key", "rb") as file:
        clave = file.read()
    cipher_suite = Fernet(clave)
    return pickle.loads(cipher_suite.decrypt(pickle.dumps(mensaje)))
    '''
    return mensaje


# Registrar un dron en AD_Registry
def connect_to_registry(alias,host,port):
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
                    ssock.sendall(alias.encode("utf-8"))
                    ret = ssock.recv(1024)
                    ret = pickle.loads(ret)
                    return ret[0], ret[1]

        except:
            print("\n\n" + '\x1b[5;30;41m' + " No se puede establecer conexión con AD_Registry. Reintentando en 5 segundos... " + '\x1b[0m')
            sleep(5)

# Registrar un dron en AD_Registry
def registrarDron(host,port):
    global alias
    global id
    alias = str(input("\n\n " + colored(">", 'green') + " Introduce un alias para el dron: "))
    id, token = connect_to_registry(alias,host,port)
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
                            json.dumps(x).encode('utf-8'))

        pos = calcularMovimiento(pos, destino)
        data = {"id": encryptMensaje(idDron), "posicion": encryptMensaje(pos)}
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
            value_deserializer=lambda x: loads(x.decode('utf-8')))
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
                aux["destino"] = decryptMensaje(aux["destino"])
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
                    sleep(2)
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
            value_deserializer=lambda x: loads(x.decode('utf-8')))
        goTo = TopicPartition('posiciones', 0)
        consumer.assign([goTo])
        consumer.seek_to_end(goTo)

        while end!=True:
            for mensaje in consumer:
                aux = mensaje.value["message"]
                aux["mapa"] = decryptMensaje(aux["mapa"])
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
def authenticate_with_engine(token, engine_ip, engine_port):
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
                ssock.sendall(token.encode("utf-8"))
                response = pickle.loads(ssock.recv(1024))
                if response[0]=='TOKEN VALIDO':
                    id = response[1]
                    return True
                else:
                    return False
    except:
        return authenticate_with_engine(token, engine_ip, engine_port)

# En la función unirseEspectaculo, después de verificar si el token no está vacío
def unirseEspectaculo(id, ip_engine, puerto_engine):
    
    token = str(input("\n\n " + colored(">", 'green') + " Introduce el token del dron: "))
    if token != "":
        if authenticate_with_engine(token, ip_engine, int(puerto_engine)):
            return True
    return False


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
            print("ERROR. El quinto argumento, si existe, ha de ser -d")
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
        id,token=connect_to_registry(alias,ip_registry,puerto_registry)
        #sleep(2)
        if authenticate_with_engine(token, ip_engine, int(puerto_engine)):
            realizarEspectaculo(puerto_colas, id)
            cerrarEspectaculo(ip_engine,puerto_engine)
            try:
                finRegistry(ip_registry,puerto_registry)
            except:
                pass
            sys.exit()
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
        print(" " + colored("1.", 'green') + " Registrar dron")
        print(" " + colored("2.", 'green') + " Unirse al espectáculo")
        print(" " + colored("3.", 'green') + " Salir")
        opcion = int(input(" " + "\n " + colored(">", 'green') + " Opción: "))
        if opcion == 1:
            id, alias = registrarDron(ip_registry,puerto_registry)
        elif opcion == 2:
            if unirseEspectaculo(id, ip_engine,puerto_engine):
                realizarEspectaculo(puerto_colas, id)
                cerrarEspectaculo(ip_engine,puerto_engine)
                try:
                    finRegistry(ip_registry,puerto_registry)
                except:
                    pass
                sys.exit()
            else:
                print("\033c")
                print(" " + '\x1b[5;30;41m' + " Autentificación fallida " + '\x1b[0m' + "\n\n")
        elif opcion == 3:
            sys.exit()
        else:
            print("\033c")
            print(" " + '\x1b[5;30;41m' + " Opción incorrecta " + '\x1b[0m' + "\n\n")

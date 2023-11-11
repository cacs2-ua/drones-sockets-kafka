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

HOST = '127.0.0.1'
PORT = 65432  # Puerto al que AD_Registry está escuchando
DATABASE_PATH = "drones.json"
DATABASE_PATH_2 = "authenticated.json"
ID_DRONE=0
ALIAS_DRONE=""
TOKEN_DRONE=""

os.system('color')

# Registrar un dron en AD_Registry
def connect_to_registry(alias,host,port):
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                s.sendall(alias.encode("utf-8"))
                token = s.recv(1024).decode("utf-8")
            return token
        except ConnectionRefusedError:
            #print("No se puede establecer conexión con AD_Registry. Reintentando en 10 segundos...")
            sleep(2)

# Registrar un dron en AD_Registry
def registrarDron(token,host,port):
    if token != "":
        print("\033c" + "\n")
        print(" " + '\x1b[5;30;41m' + " El dron \"" +  alias + "\" ya está registrado " + '\x1b[0m' + "\n\n")
        return id, token, alias
    alias = str(input("\n\n " + colored(">", 'green') + " Introduce un alias para el dron: "))

    token = connect_to_registry(alias,host,port)
    id = get_next_drone_id()
    ID_DRON=id
    print("\033c" + "\n")
    print(" " + '\x1b[6;30;42m' + " Dron \"" + alias + "\" registrado correctamente con ID = " + str(id) + " " + '\x1b[0m' + "\n\n")
    return id, token, alias


"""
# Unirse al espectaculo de drones
def unirseEspectaculo(id, token, puerto_engine):

    if(token==""):
        print("\033c" + "\n")
        print(" " + '\x1b[5;30;41m' + " No está registrado el dron " + '\x1b[0m' + "\n\n")
        return False
    return True
"""
def get_next_drone_id():
    with open(DATABASE_PATH, 'r') as file:
        data = json.load(file)

    if not data["drones"]:
        return 1
    return int(data["drones"][-1]["id"]) + 1

# Comprobar conexion con el Engine
def connectionCheck(puerto_colas, idDron):
    return

# Enviar movimiento del dron al Engine
def enviarMovimiento(pos, destino, puerto_colas, idDron):
    try:
        producer = KafkaProducer(bootstrap_servers=[puerto_colas],
                            value_serializer=lambda x: 
                            json.dumps(x).encode('utf-8'))

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
        mensaje = {"id": idDron, "posicion": pos}
        producer.send('movimientos', value=mensaje)
        producer.flush()
        return pos

    except:
        raise Exception()

# Obtener posicion a la que se debe mover el dron
def getDestino(puerto_colas, idDron):
    end = False
    first = True
    pos = (0,0)
    try:
        consumer2 = KafkaConsumer(
            bootstrap_servers=[puerto_colas],
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='drones',
            value_deserializer=lambda x: loads(x.decode('utf-8')))
        goTo = TopicPartition('destinos', 0)
        consumer2.assign([goTo])
        consumer2.seek_to_end(goTo)

        while end!=True:
            for mensaje in consumer2:
                '''
                if first:
                    con = threading.Thread(target=connectionCheck, args=(puerto_colas, idDron, ))
                    con.start()
                    first = False
                '''
                aux = mensaje.value
                if aux["destino"][0]=="Stop" and aux["destino"][1] == idDron:
                    end = True
                    break
                elif aux["destino"][0]=="Wait" and aux["destino"][1] == idDron:
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
                    sleep(1)
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
                aux = mensaje.value
                print("\033c")
                if(comprobarMapa(aux["mapa"])):
                    print("  " + '\x1b[6;30;47m' + " MAPA DEL ESPECTACULO " + '\x1b[0m', end="                 ")
                    if aux["completo"]==True:
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
                                if aux["mapa"][i-1][j-1][1]!=True:
                                    color = '\x1b[5;30;41m'
                                else:
                                    color = '\x1b[6;30;42m'
                                if aux["mapa"][i-1][j-1][0]==0:
                                    print("    ", end = " ")
                                elif aux["mapa"][i-1][j-1][0]<10:
                                    print(color + "  " + str(aux["mapa"][i-1][j-1][0]) + " " + '\x1b[0m', end = " ")
                                else:
                                    print(color + " " + str(aux["mapa"][i-1][j-1][0]) + " " + '\x1b[0m', end = " ")
                    print("\n")
                print('\x1b[6;30;42m' + " Dron: " + str(idDron) + " " + '\x1b[0m' + "\n")
                if aux["completo"]==True:
                    sleep(1)
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

def buscaDronPorToken(token):
    # Buscamos dentro de la lista de drones
    with open('drones.json', 'r') as file:
        data = json.load(file)
    for dron in data['drones']:
        if dron['token'] == token:
            return dron['id'], dron['alias']
    return None, None

# Función para enviar token al AD_Engine para autenticación
def authenticate_with_engine(token, engine_ip, engine_port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((engine_ip, engine_port))
            s.sendall(token.encode("utf-8"))
            
            response = s.recv(1024).decode("utf-8")
            if response == 'TOKEN VALIDO':
                print("Token validado con éxito. Unido al espectáculo.")
                with open('authenticated.json', 'r') as file:
                    data = json.load(file)
                id,alias=buscaDronPorToken(token)
                with open('authenticated.json', 'r+') as file:
                    data = json.load(file)
                    data["authenticated"].append({"id": id, "alias": alias, "token": token})
                    file.seek(0)  # Volver al principio del archivo
                    json.dump(data, file, indent=4)  # Guardar los cambios en el archivo
                return True
            else:
                print("Token inválido.")
                return False
    except ConnectionRefusedError:
        authenticate_with_engine(token, engine_ip, engine_port)

# En la función unirseEspectaculo, después de verificar si el token no está vacío
def unirseEspectaculo(id, token, ip_engine, puerto_engine):
    # ... código existente ...
    if token != "":
        if authenticate_with_engine(token, ip_engine, int(puerto_engine)):
            print("Uniéndose al espectáculo")
            sleep(1)
            return True
            #realizarEspectaculo(puerto_colas)
            #sys.exit()
    return False

def receiveNumberOfDrones(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
        numberOfDrones = s.recv(1024).decode('utf-8')
        s.close()
        try:
            return int(numberOfDrones)
        except ValueError:
            print("Exception of type ValueError")
            return None
    except ConnectionRefusedError:
        print("No se puede establecer conexión con AD_Engine. Reintentando...")
        sleep(1)
        return receiveNumberOfDrones(host, port)

def mainreceiveNumberOfDrones(host, port):
    receiveNumberOfDrones(host, port)



def numeroElementosJson(ruta_archivo_json):
    try:
        with open(ruta_archivo_json, 'r') as archivo:
            datos = json.load(archivo)
            # Asumimos que la lista de elementos está bajo la clave 'authenticated'
            numero_de_elementos = len(datos['authenticated'])
            return numero_de_elementos
    except FileNotFoundError:
        print("El archivo no fue encontrado.")
        return None
    except json.JSONDecodeError:
        print("El archivo no está en formato JSON válido.")
        return None
    except KeyError:
        print("La clave 'authenticated' no existe en el JSON.")
        return None

def mainNumeroElementosJson(ruta_archivo_json):
    return mainNumeroElementosJson(ruta_archivo_json)

# Parte principal del programa
if __name__ == "__main__":

    # Argumentos de linea de parametros
    if len(sys.argv)!=4:
        print("\033c")
        sys.exit("\n " + '\x1b[5;30;41m' + " Numero de argumentos incorrecto " + '\x1b[0m' + "\n\n " + colored(">", 'green') + " Uso:  python AD_Drone.py <IP:Puerto Engine> <IP:Puerto Colas> <IP:Puerto Registry>")
    ip_engine,puerto_engine = sys.argv[1].split(':')
    puerto_engine=int(puerto_engine)
    puerto_colas = sys.argv[2]
    ip_registry, puerto_registry = sys.argv[3].split(':')
    #numberOfDrone=0
    #numberOfDrones=receiveNumberOfDrones(ip_engine,puerto_engine)
    #print("Number of drones received: " +str(numberOfDrones))
    #sleep(3)
    # Variables del dron
    id : int
    token : str = ""
    alias : str = ""

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
            if check == True:
                id, token, alias = registrarDron(token,ip_registry, int(puerto_registry))
                check=False
            else:
                print(" " + '\x1b[5;30;41m' + " El dron \"" +  alias + "\" ya está registrado " + '\x1b[0m' + "\n\n")
        elif opcion == 2:
            if unirseEspectaculo(id, token, ip_engine,puerto_engine):
                print("Token validado con éxito. Uniéndose al espectáculo.")
                numberOfAuthenticatedDrones=numeroElementosJson(DATABASE_PATH_2)
                #print("Hay " + str (numberOfAuthenticatedDrones) + " drones autenticados")
                realizarEspectaculo(puerto_colas, id)
                sys.exit()
        elif opcion == 3:
            sys.exit()
    
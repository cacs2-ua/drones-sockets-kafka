import json

try:
# Leer el archivo JSON
    with open('drones.json', 'r') as archivo:
        data = json.load(archivo)
        archivo.close()

    # Borrar todas las entradas bajo 'drones'
    data['drones'] = []

    # Escribir los cambios en el archivo JSON
    with open('drones.json', 'w') as archivo:
        json.dump(data, archivo, indent=4)
        archivo.close()
except:
    data = { "drones": [] }
    with open('drones.json', 'w') as file:
        json.dump(data, file, indent=4)
        file.close()

try:
    with open('mapa.json', 'r') as file:
        data = json.load(file)
        file.close()

    data["mapa"] = []

    with open('mapa.json', 'w') as file:
        json.dump(data, file)
        file.close()
except:
    data = { "mapa": [] }
    with open('mapa.json', 'w') as file:
        json.dump(data, file, indent=4)
        file.close()
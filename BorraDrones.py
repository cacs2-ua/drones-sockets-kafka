import json

# Ruta al archivo JSON
ruta_archivo_json = 'drones.json'

# Leer el archivo JSON
with open(ruta_archivo_json, 'r') as archivo:
    data = json.load(archivo)

# Borrar todas las entradas bajo 'drones'
data['drones'] = []

# Escribir los cambios en el archivo JSON
with open(ruta_archivo_json, 'w') as archivo:
    json.dump(data, archivo, indent=4)

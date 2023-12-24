import json

def reset_mapa_json(file_path):
    try:
        # Open the existing mapa.json file
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Check if 'mapa' key exists and is a list
        if 'mapa' in data and isinstance(data['mapa'], list):
            # Iterate through each row and set the first element of each cell to 0
            for row in data['mapa']:
                for cell in row:
                    cell[0] = 0

        # Write the modified data back to the file
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

        print("Mapa.json has been reset successfully.")

    except json.JSONDecodeError:
        print("Error: The file is not a valid JSON.")
    except FileNotFoundError:
        print("Error: The file was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    # Call the function with the path to your mapa.json file
    reset_mapa_json('mapa.json')

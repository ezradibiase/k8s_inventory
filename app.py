from flask import Flask, render_template, jsonify
import json

app = Flask(__name__)

# Carica il file JSON con le informazioni del cluster Kubernetes
def load_k8s_inventory():

    try:
        with open('k8s_inventory.json', 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Errore nel caricamento del file JSON: {e}")
        raise


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/data', methods=['GET'])

def get_inventory():
    try:
        inventory = load_k8s_inventory()  # Carica l'inventario
        print(f"Dati caricati con successo: {len(inventory)} risorse")  # Stampa solo il numero di risorse
        return jsonify(inventory)
    except Exception as e:
        print(f"Errore durante il caricamento dei dati: {e}")
        traceback.print_exc()  # Stampa la traccia dello stack dell'eccezione
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

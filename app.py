#!/usr/bin/env python3

from flask import Flask, render_template, jsonify
from kubernetes import client, config
import json
import traceback
import os
import logging

app = Flask(__name__)

# Configura il logger per ottenere informazioni dettagliate
# logging.basicConfig(level=logging.DEBUG)

# Recupera la variabile di ambiente KUBECONFIG, se presente, altrimenti usa un percorso di default
kubeconfig_path = os.environ.get('KUBECONFIG', '/home/ezrad/rancher-kubeconfig-sbe-avm-cert.yaml')
logging.debug(f"Usando KUBECONFIG: {kubeconfig_path}")

def load_k8s_inventory():
    try:
        # Carica la configurazione dal file KUBECONFIG o dalla configurazione di default
        config.load_kube_config()
        logging.debug("Configurazione Kubernetes caricata con successo.")

        # Creare istanze dei vari client
        v1 = client.CoreV1Api()
        apps_v1 = client.AppsV1Api()

        # Recupera Deployments
        deployments = apps_v1.list_deployment_for_all_namespaces(watch=False).items
        deployments_data = []
        for dep in deployments:
            deployments_data.append({
                "name": dep.metadata.name,
                "namespace": dep.metadata.namespace,
                "replicas": dep.spec.replicas,
                "available_replicas": dep.status.available_replicas or 0,
                "creation_timestamp": dep.metadata.creation_timestamp.isoformat(),
                "labels": dep.metadata.labels
            })

        # Recupera StatefulSets
        statefulsets = apps_v1.list_stateful_set_for_all_namespaces(watch=False).items
        statefulsets_data = []
        for sts in statefulsets:
            statefulsets_data.append({
                "name": sts.metadata.name,
                "namespace": sts.metadata.namespace,
                "replicas": sts.spec.replicas,
                "available_replicas": sts.status.ready_replicas or 0,
                "creation_timestamp": sts.metadata.creation_timestamp.isoformat(),
                "labels": sts.metadata.labels
            })

        # Recupera Nodi
        nodes = v1.list_node(watch=False).items
        nodes_data = []
        for node in nodes:
            # Serializza manualmente le condizioni
            conditions = []
            if node.status.conditions:
                for condition in node.status.conditions:
                    conditions.append({
                        'type': condition.type,
                        'status': condition.status,
                        'last_heartbeat_time': condition.last_heartbeat_time.isoformat() if condition.last_heartbeat_time else None,
                        'last_transition_time': condition.last_transition_time.isoformat() if condition.last_transition_time else None,
                        'reason': condition.reason,
                        'message': condition.message
                    })

            nodes_data.append({
                "name": node.metadata.name,
                "labels": node.metadata.labels,
                "annotations": node.metadata.annotations,
                "conditions": conditions,  # Condizioni serializzabili
                "capacity": node.status.capacity,
                "allocatable": node.status.allocatable,
                "creation_timestamp": node.metadata.creation_timestamp.isoformat()
            })

        return {
            "deployments": deployments_data,
            "statefulsets": statefulsets_data,
            "nodes": nodes_data
        }
    except Exception as e:
        logging.error(f"Errore nel caricamento dei dati Kubernetes: {e}")
        traceback.print_exc()
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data', methods=['GET'])
def get_inventory():
    try:
        inventory = load_k8s_inventory()
        deployments_count = len(inventory.get('deployments', []))
        statefulsets_count = len(inventory.get('statefulsets', []))
        nodes_count = len(inventory.get('nodes', []))
        print(f"Dati caricati con successo: {deployments_count} deployments, {statefulsets_count} statefulsets, {nodes_count} nodes")
        return jsonify(inventory)
    except Exception as e:
        print(f"Errore durante il caricamento dei dati: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    try:
        logging.debug("Chiamata a /api/nodes ricevuta")
        v1 = client.CoreV1Api()
        logging.debug("Creazione dell'istanza CoreV1Api completata.")

        # Imposta un timeout di 10 secondi
        nodes = v1.list_node(timeout_seconds=10)
        logging.debug(f"Numero di nodi recuperati: {len(nodes.items)}")

        node_info = []
        for node in nodes.items:
            status = "Unknown"
            conditions = []
            if node.status.conditions:
                # Itera attraverso le condizioni e converte in dizionari
                for condition in node.status.conditions:
                    conditions.append({
                        'type': condition.type,
                        'status': condition.status,
                        'last_heartbeat_time': condition.last_heartbeat_time.isoformat() if condition.last_heartbeat_time else None,
                        'last_transition_time': condition.last_transition_time.isoformat() if condition.last_transition_time else None,
                        'reason': condition.reason,
                        'message': condition.message
                    })
                    if condition.type == "Ready":
                        status = condition.status
            node_info.append({
                'name': node.metadata.name,
                'status': status,
                'conditions': conditions
            })
        logging.debug(f"Nodes: {node_info}")
        return jsonify(node_info)
    except client.rest.ApiException as e:
        logging.error(f"Errore API di Kubernetes: {e}")
        return jsonify({'error': f"API Kubernetes Error: {e}"}), 500
    except Exception as e:
        logging.error(f"Errore nel recupero dei nodi: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)


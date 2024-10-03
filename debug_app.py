#!/usr/bin/env python3

from flask import Flask, jsonify
import os
from kubernetes import client, config
import traceback
import logging

app = Flask(__name__)

# Configura il logger per ottenere informazioni dettagliate
logging.basicConfig(level=logging.DEBUG)

# Recupera la variabile di ambiente KUBECONFIG, se presente, altrimenti usa un percorso di default
kubeconfig_path = os.environ.get('KUBECONFIG', '/home/ezrad/rancher-kubeconfig-sbe-avm-cert.yaml')
logging.debug(f"Usando KUBECONFIG: {kubeconfig_path}")

def load_k8s_inventory():
    try:
        # Carica la configurazione di Kubernetes
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
            nodes_data.append({
                "name": node.metadata.name,
                "labels": node.metadata.labels,
                "annotations": node.metadata.annotations,
                "conditions": node.status.conditions,
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
    return "Kubernetes Inventory Application"

@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    try:
        logging.debug("Chiamata a /api/nodes ricevuta")
        v1 = client.CoreV1Api()
        nodes = v1.list_node()
        node_info = [{'name': node.metadata.name, 'status': node.status.conditions[0].type if node.status.conditions else "Unknown"} for node in nodes.items]
        logging.debug(f"Nodes: {node_info}")
        return jsonify(node_info)
    except Exception as e:
        logging.error(f"Errore nel recupero dei nodi: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/data', methods=['GET'])
def get_inventory():
    try:
        logging.debug("Chiamata a /data ricevuta")
        inventory = load_k8s_inventory()
        deployments_count = len(inventory.get('deployments', []))
        statefulsets_count = len(inventory.get('statefulsets', []))
        nodes_count = len(inventory.get('nodes', []))
        logging.debug(f"Dati caricati con successo: {deployments_count} deployments, {statefulsets_count} statefulsets, {nodes_count} nodes")
        return jsonify(inventory)
    except Exception as e:
        logging.error(f"Errore durante il caricamento dei dati: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)


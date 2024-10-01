#!/usr/bin/env python3

import json
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from datetime import datetime

def load_kube_config():
    """
    Carica la configurazione di Kubernetes.
    Prova prima la configurazione in-cluster, poi il file kubeconfig locale.
    """
    try:
        config.load_incluster_config()
        print("Configurazione in-cluster caricata.")
    except config.ConfigException:
        config.load_kube_config()
        print("Configurazione kubeconfig locale caricata.")

def get_deployments(api_instance, namespace):
    try:
        deployments = api_instance.list_namespaced_deployment(namespace=namespace)
        deployment_list = []
        for dep in deployments.items:
            deployment_list.append({
                "name": dep.metadata.name,
                "namespace": dep.metadata.namespace,
                "replicas": dep.spec.replicas,
                "available_replicas": dep.status.available_replicas,
                "labels": dep.metadata.labels,
                "creation_timestamp": dep.metadata.creation_timestamp.isoformat() if dep.metadata.creation_timestamp else None
            })
        return deployment_list
    except ApiException as e:
        print(f"Errore nel recuperare i Deployments nel namespace {namespace}: {e}")
        return []

def get_replicasets(api_instance, namespace):
    try:
        replicasets = api_instance.list_namespaced_replica_set(namespace=namespace)
        replicaset_list = []
        for rs in replicasets.items:
            replicaset_list.append({
                "name": rs.metadata.name,
                "namespace": rs.metadata.namespace,
                "replicas": rs.spec.replicas,
                "available_replicas": rs.status.available_replicas,
                "labels": rs.metadata.labels,
                "creation_timestamp": rs.metadata.creation_timestamp.isoformat() if rs.metadata.creation_timestamp else None
            })
        return replicaset_list
    except ApiException as e:
        print(f"Errore nel recuperare i ReplicaSets nel namespace {namespace}: {e}")
        return []

def get_statefulsets(api_instance, namespace):
    try:
        statefulsets = api_instance.list_namespaced_stateful_set(namespace=namespace)
        statefulset_list = []
        for sts in statefulsets.items:
            statefulset_list.append({
                "name": sts.metadata.name,
                "namespace": sts.metadata.namespace,
                "replicas": sts.spec.replicas,
                "available_replicas": sts.status.ready_replicas,
                "labels": sts.metadata.labels,
                "creation_timestamp": sts.metadata.creation_timestamp.isoformat() if sts.metadata.creation_timestamp else None
            })
        return statefulset_list
    except ApiException as e:
        print(f"Errore nel recuperare i StatefulSets nel namespace {namespace}: {e}")
        return []

def get_nodes(api_instance):
    try:
        nodes = api_instance.list_node()
        node_list = []
        for node in nodes.items:
            node_conditions = [condition.to_dict() for condition in node.status.conditions]  # Converti V1NodeCondition in dict
            node_list.append({
                "name": node.metadata.name,
                "labels": node.metadata.labels,
                "annotations": node.metadata.annotations,
                "status": node_conditions,  # Condizioni dei nodi convertite
                "capacity": node.status.capacity,
                "allocatable": node.status.allocatable,
                "creation_timestamp": node.metadata.creation_timestamp.isoformat() if node.metadata.creation_timestamp else None
            })
        return node_list
    except ApiException as e:
        print(f"Errore nel recuperare i nodi: {e}")
        return []

# Encoder personalizzato per JSON che gestisce oggetti datetime
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def main():
    load_kube_config()

    # Inizializza le API
    apps_v1 = client.AppsV1Api()
    core_v1 = client.CoreV1Api()

    # Recupera tutti i namespace
    try:
        namespaces = core_v1.list_namespace()
        namespace_names = [ns.metadata.name for ns in namespaces.items]
    except ApiException as e:
        print(f"Errore nel recuperare i namespaces: {e}")
        return

    # Inizializza l'inventario
    inventory = {
        "deployments": [],
        "replicasets": [],
        "statefulsets": [],
        "nodes": []
    }

    # Recupera Deployments, ReplicaSets e StatefulSets per ogni namespace
    for ns in namespace_names:
        print(f"Recupero risorse nel namespace: {ns}")
        inventory["deployments"].extend(get_deployments(apps_v1, ns))
        inventory["replicasets"].extend(get_replicasets(apps_v1, ns))
        inventory["statefulsets"].extend(get_statefulsets(apps_v1, ns))

    # Recupera i nodi
    print("Recupero nodi del cluster.")
    inventory["nodes"] = get_nodes(core_v1)

    # Scrivi l'inventario in un file JSON usando l'encoder personalizzato
    with open("k8s_inventory.json", "w") as f:
        json.dump(inventory, f, indent=4, cls=DateTimeEncoder)

    print("Inventario salvato in k8s_inventory.json")

if __name__ == "__main__":
    main()

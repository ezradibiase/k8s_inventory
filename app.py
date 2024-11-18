#!/usr/bin/env python3

import io
import json
import traceback
import os
import logging
from flask import Flask, render_template, jsonify, send_file, request
from kubernetes import client, config
from weasyprint import HTML, CSS

app = Flask(__name__)

# Configure logging
# logging.basicConfig(level=logging.DEBUG)

# Retrieve KUBECONFIG path from environment or use default
kubeconfig_path = os.environ.get('KUBECONFIG', '/home/ezrad/.kube/one-config.yaml')
logging.debug(f"Using KUBECONFIG: {kubeconfig_path}")


def add_page_number(canvas, doc):
    from reportlab.lib.units import mm  # Ensure this import
    page_num = canvas.getPageNumber()
    text = f"Page {page_num}"
    canvas.setFont('Helvetica', 9)
    canvas.drawRightString(200 * mm, 15 * mm, text)


@app.route('/generate_pdf', methods=['GET'])
def generate_pdf():
    try:
        context = request.args.get('context', default=None, type=str)
        resource_type = request.args.get('resource_type', default='', type=str).lower()
        namespace = request.args.get('namespace', default='', type=str)

        inventory = load_k8s_inventory(context=context)

        # Filter data
        filtered_inventory = {
            "deployments": [],
            "statefulsets": [],
            "nodes": []
        }

        if resource_type in ['deployment', '']:

            filtered_inventory['deployments'] = [
                dep for dep in inventory['deployments']
                if namespace == '' or dep['namespace'] == namespace
            ]

        if resource_type in ['statefulset', '']:
            filtered_inventory['statefulsets'] = [
                sts for sts in inventory['statefulsets']
                if namespace == '' or sts['namespace'] == namespace
            ]

        if resource_type in ['node', '']:
            filtered_inventory['nodes'] = inventory['nodes']  # Nodes do not have namespaces

        logging.debug(f"Filtered inventory: {json.dumps(filtered_inventory, indent=2)}")

        # Define headers and keys
        headers = {
            "deployments": ["Name", "Namespace", "Replicas", "Available Replicas", "Creation Timestamp", "Labels"],
            "statefulsets": ["Name", "Namespace", "Replicas", "Available Replicas", "Creation Timestamp", "Labels"],
            "nodes": ["Name", "Status", "Conditions"]
        }

        keys = {
            "deployments": ["name", "namespace", "replicas", "available_replicas", "creation_timestamp", "labels"],
            "statefulsets": ["name", "namespace", "replicas", "available_replicas", "creation_timestamp", "labels"],
            "nodes": ["name", "status", "conditions"]
        }

        # Prepare data for the template
        template_data = {
            "inventory": filtered_inventory,
            "headers": headers,
            "keys": keys
        }

        # Render HTML template
        rendered_html = render_template('report.html', **template_data)

        # Generate PDF with WeasyPrint
        pdf_file = HTML(string=rendered_html, base_url=request.base_url).write_pdf()

        # Create in-memory buffer
        buffer = io.BytesIO(pdf_file)

        # Return PDF as response
        return send_file(buffer, as_attachment=True, download_name="k8s_inventory.pdf", mimetype='application/pdf')

    except Exception as e:
        logging.error(f"Error generating PDF: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def load_k8s_inventory(context=None):
    try:
        # Load kubeconfig with the specified context if provided
        if context:
            config.load_kube_config(config_file=kubeconfig_path, context=context)
            logging.debug(f"Kubernetes configuration loaded with context: {context}")
        else:
            config.load_kube_config(config_file=kubeconfig_path)
            logging.debug("Kubernetes configuration loaded with default context.")

        # Create API clients
        v1 = client.CoreV1Api()
        apps_v1 = client.AppsV1Api()

        # Get Deployments
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

        # Get StatefulSets
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

        # Get Nodes
        nodes = v1.list_node(watch=False).items
        nodes_data = []
        for node in nodes:
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
                "conditions": conditions,
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
        logging.error(f"Error loading Kubernetes data: {e}")
        traceback.print_exc()
        raise


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/data', methods=['GET'])
def get_inventory():
    try:
        context = request.args.get('context', default=None, type=str)
        resource_type = request.args.get('resource_type', default='', type=str).lower()
        namespace = request.args.get('namespace', default='', type=str)

        inventory = load_k8s_inventory(context=context)

        # Filter data
        filtered_inventory = {
            "deployments": [],
            "statefulsets": [],
            "nodes": []
        }

        if resource_type in ['deployment', '']:
            filtered_inventory['deployments'] = [
                dep for dep in inventory['deployments']
                if namespace == '' or dep['namespace'] == namespace
            ]

        if resource_type in ['statefulset', '']:
            filtered_inventory['statefulsets'] = [
                sts for sts in inventory['statefulsets']
                if namespace == '' or sts['namespace'] == namespace
            ]

        if resource_type in ['node', '']:
            filtered_inventory['nodes'] = inventory['nodes']  # Nodes do not have namespaces

        logging.debug(f"Filtered inventory: {json.dumps(filtered_inventory, indent=2)}")

        return jsonify(filtered_inventory)
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/test_report')
def test_report():
    # Dati di esempio
    sample_inventory = {
        "deployments": [
            {
                "name": "app1",
                "namespace": "default",
                "replicas": 3,
                "available_replicas": 3,
                "creation_timestamp": "2024-04-01T12:34:56Z",
                "labels": {"app": "myapp", "tier": "backend"}
            }
        ],
        "statefulsets": [
            {
                "name": "sts1",
                "namespace": "prod",
                "replicas": 2,
                "available_replicas": 2,
                "creation_timestamp": "2024-04-02T10:20:30Z",
                "labels": {"app": "mysts", "tier": "frontend"}
            }
        ],
        "nodes": [
            {
                "name": "node1",
                "status": "Ready",
                "conditions": [
                    {"type": "Ready", "status": "True"}
                ]
            }
        ]
    }

    headers = {
        "deployments": ["Name", "Namespace", "Replicas", "Available Replicas", "Creation Timestamp", "Labels"],
        "statefulsets": ["Name", "Namespace", "Replicas", "Available Replicas", "Creation Timestamp", "Labels"],
        "nodes": ["Name", "Status", "Conditions"]
    }

    keys = {
        "deployments": ["name", "namespace", "replicas", "available_replicas", "creation_timestamp", "labels"],
        "statefulsets": ["name", "namespace", "replicas", "available_replicas", "creation_timestamp", "labels"],
        "nodes": ["name", "status", "conditions"]
    }

    template_data = {
        "inventory": sample_inventory,
        "headers": headers,
        "keys": keys
    }

    return render_template('report.html', **template_data)


# @app.route('/contexts', methods=['GET'])
# def get_contexts():
#     try:
#         kubeconfig = config.kube_config.KubeConfigLoader(
#             config.kube_config.KUBE_CONFIG_DEFAULT_LOCATION
#         )
#         contexts = kubeconfig.config['contexts']
#         context_names = [context['name'] for context in contexts]
#         logging.debug(f"Available contexts: {context_names}")
#         return jsonify({"contexts": context_names})
#     except Exception as e:
#         logging.error(f"Error fetching contexts: {e}")
#         traceback.print_exc()
#         return jsonify({"error": str(e)}), 500

@app.route('/contexts', methods=['GET'])
def get_contexts():
    try:
        contexts, active_context = config.list_kube_config_contexts(config_file=kubeconfig_path)
        context_names = [context['name'] for context in contexts]
        logging.debug(f"Available contexts: {context_names}")
        return jsonify({"contexts": context_names})
    except FileNotFoundError as fnf_error:
        logging.error(fnf_error)
        return jsonify({"error": str(fnf_error)}), 404
    except Exception as e:
        logging.error(f"Error fetching contexts: {e}")
        traceback.print_exc()
        return jsonify({"error": "Failed to retrieve Kubernetes contexts."}), 500


@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    try:
        context = request.args.get('context', default=None, type=str)
        logging.debug("Received call to /api/nodes")
        
        if context:
            config.load_kube_config(config_file=kubeconfig_path, context=context)
            logging.debug(f"Kubernetes configuration loaded with context: {context}")
        else:
            config.load_kube_config(config_file=kubeconfig_path)
            logging.debug("Kubernetes configuration loaded with default context.")

        v1 = client.CoreV1Api()
        logging.debug("CoreV1Api instance created.")

        nodes = v1.list_node(timeout_seconds=10)
        logging.debug(f"Number of nodes retrieved: {len(nodes.items)}")

        node_info = []
        for node in nodes.items:
            status = "Unknown"
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
        logging.error(f"Kubernetes API Error: {e}")
        return jsonify({'error': f"Kubernetes API Error: {e}"}), 500
    except Exception as e:
        logging.error(f"Error retrieving nodes: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)


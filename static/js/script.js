$(document).ready(function() {
    // Inizializza DataTables
    var deploymentsTable = $('#deployments-table').DataTable();
    var replicasetsTable = $('#replicasets-table').DataTable();
    var statefulsetsTable = $('#statefulsets-table').DataTable();
    var nodesTable = $('#nodes-table').DataTable();

    // Funzione per caricare e popolare le tabelle
    function loadInventory() {
        $.ajax({
            url: '/api/inventory',
            method: 'GET',
            dataType: 'json',
            success: function(data) {
                populateDeployments(data.deployments);
                populateReplicaSets(data.replicasets);
                populateStatefulSets(data.statefulsets);
                populateNodes(data.nodes);
            },
            error: function(error) {
                console.error('Errore nel recupero dell\'inventario:', error);
            }
        });
    }

    // Funzioni per popolare le tabelle
    function populateDeployments(deployments) {
        deploymentsTable.clear();
        deployments.forEach(function(dep) {
            deploymentsTable.row.add([
                dep.name,
                dep.namespace,
                dep.replicas,
                dep.available_replicas || 0,
                formatLabels(dep.labels),
                dep.creation_timestamp
            ]);
        });
        deploymentsTable.draw();
    }

    function populateReplicaSets(replicasets) {
        replicasetsTable.clear();
        replicasets.forEach(function(rs) {
            replicasetsTable.row.add([
                rs.name,
                rs.namespace,
                rs.replicas,
                rs.available_replicas || 0,
                formatLabels(rs.labels),
                rs.creation_timestamp
            ]);
        });
        replicasetsTable.draw();
    }

    function populateStatefulSets(statefulsets) {
        statefulsetsTable.clear();
        statefulsets.forEach(function(sts) {
            statefulsetsTable.row.add([
                sts.name,
                sts.namespace,
                sts.replicas,
                sts.available_replicas || 0,
                formatLabels(sts.labels),
                sts.creation_timestamp
            ]);
        });
        statefulsetsTable.draw();
    }

    function populateNodes(nodes) {
        nodesTable.clear();
        nodes.forEach(function(node) {
            nodesTable.row.add([
                node.name,
                formatLabels(node.labels),
                formatAnnotations(node.annotations),
                formatConditions(node.status),
                formatCapacity(node.capacity),
                formatCapacity(node.allocatable),
                node.creation_timestamp
            ]);
        });
        nodesTable.draw();
    }

    // Funzioni di formattazione
    function formatLabels(labels) {
        if (!labels) return '';
        return Object.entries(labels).map(([key, value]) => `${key}: ${value}`).join(', ');
    }

    function formatAnnotations(annotations) {
        if (!annotations) return '';
        return Object.entries(annotations).map(([key, value]) => `${key}: ${value}`).join(', ');
    }

    function formatConditions(conditions) {
        if (!conditions) return '';
        return conditions.map(cond => `${cond.type}: ${cond.status} (${cond.reason})`).join('; ');
    }

    function formatCapacity(capacity) {
        if (!capacity) return '';
        return Object.entries(capacity).map(([key, value]) => `${key}: ${value}`).join(', ');
    }

    // Carica l'inventario all'avvio
    loadInventory();

    // Gestisci i filtri
    $('.resource-filter').change(function() {
        var resource = $(this).val();
        var isChecked = $(this).is(':checked');
        if (isChecked) {
            $(`#${resource}-section`).show();
        } else {
            $(`#${resource}-section`).hide();
        }
    });
});


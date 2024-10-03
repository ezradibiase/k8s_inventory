$(document).ready(function() {
    // Carica i dati dall'endpoint Flask
    $.getJSON('/data', function(data) {
        console.log("Dati ricevuti:", data); // Log dei dati ricevuti

        let tableData = [];

        // Processa deployments
        if (data.deployments) {
            data.deployments.forEach(function(item) {
                tableData.push({
                    "Resource Type": "Deployment",
                    "Name": item.name || "N/A",
                    "Namespace": item.namespace || "N/A",
                    "Replicas": item.replicas || "N/A",
                    "Available Replicas": item.available_replicas || "N/A",
                    "Creation Timestamp": item.creation_timestamp || "N/A",
                    "Labels": item.labels ? JSON.stringify(item.labels) : "N/A"
                });
            });
        }

        // Processa statefulsets
        if (data.statefulsets) {
            data.statefulsets.forEach(function(item) {
                tableData.push({
                    "Resource Type": "StatefulSet",
                    "Name": item.name || "N/A",
                    "Namespace": item.namespace || "N/A",
                    "Replicas": item.replicas || "N/A",
                    "Available Replicas": item.available_replicas || "N/A",
                    "Creation Timestamp": item.creation_timestamp || "N/A",
                    "Labels": item.labels ? JSON.stringify(item.labels) : "N/A"
                });
            });
        }

        // Processa nodes
        if (data.nodes) {
            data.nodes.forEach(function(item) {
                tableData.push({
                    "Resource Type": "Node",
                    "Name": item.name || "N/A",
                    "Namespace": "N/A",
                    "Replicas": "N/A",
                    "Available Replicas": "N/A",
                    "Creation Timestamp": item.creation_timestamp || "N/A",
                    "Labels": item.labels ? JSON.stringify(item.labels) : "N/A"
                });
            });
        }

        console.log("Table Data:", tableData); // Log dei dati della tabella

        // Inizializza DataTables
        let table = $('#inventory-table').DataTable({
            data: tableData,
            columns: [
                { data: 'Resource Type' },
                { data: 'Name' },
                { data: 'Namespace' },
                { data: 'Replicas' },
                { data: 'Available Replicas' },
                { data: 'Creation Timestamp' },
                { data: 'Labels' }
            ],
            destroy: true, // Permette di ricreare la tabella se esiste già
            responsive: true
        });

        // Aggiungi filtro per tipo di risorsa
        $('#resource-type').on('change', function() {
            let filterValue = this.value;
            table.column(0).search(filterValue).draw();
        });
    }).fail(function(jqXHR, textStatus, errorThrown) {
        console.error('Errore nel caricamento dei dati:', textStatus, errorThrown);
    });
});

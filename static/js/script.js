// Aggiungi l'evento per il bottone Genera PDF
document.getElementById('generate-pdf').addEventListener('click', function() {
    // Raccogli i dati dei filtri
    const resourceType = document.getElementById('resource-type').value;
    const namespace = document.getElementById('namespaceFilter').value;

    // Invia una richiesta GET a /generate_pdf con i parametri dei filtri
    const url = `/generate_pdf?resource_type=${resourceType}&namespace=${namespace}`;
    window.location.href = url; // Ricarica la pagina per scaricare il PDF
});

$(document).ready(function() {
    $.getJSON("/data", function(data) {
        console.log("Dati ricevuti:", data); // Log dei dati ricevuti

        let tableData = [];
        let namespaces = new Set();

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

                if (item.namespace) {
                    namespaces.add(item.namespace);
                }
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

                if (item.namespace) {
                    namespaces.add(item.namespace);
                }
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

                // I nodi generalmente non hanno namespace, quindi non aggiungiamo
            });
        }

        console.log("Table Data:", tableData); // Log dei dati della tabella

        // Popola il filtro per i namespace
        namespaces.forEach(function(ns) {
            $('#namespaceFilter').append(new Option(ns, ns));
        });

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

        // Filtra la tabella in base al tipo di risorsa selezionato
        $('#resource-type').on('change', function() {
            let filterValue = this.value;
            table.column(0).search(filterValue).draw();
        });

        // Filtra la tabella in base al namespace selezionato
        $('#namespaceFilter').on('change', function() {
            let filterValue = this.value;
            table.column(2).search(filterValue).draw(); // La colonna 2 è 'Namespace'
        });
    }).fail(function(jqXHR, textStatus, errorThrown) {
        console.error('Errore nel caricamento dei dati:', textStatus, errorThrown);
    });
});


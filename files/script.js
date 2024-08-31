// Fill the trabajadores table
function getTrabajadores() {
    var trabajadoresTbody = document.getElementById('TrabajadoresTable').getElementsByTagName('tbody')[0];
    fetch('/list/trabajadores')
        .then(response => response.json())
        .then(data => {
            data.forEach(trabajador => {
                // Adding a row to the table
                let row = trabajadoresTbody.insertRow();
                row.insertCell(0).textContent = trabajador[0];
                row.insertCell(1).textContent = trabajador[1];
                row.insertCell(2).textContent = trabajador[2];
                row.insertCell(3).textContent = trabajador[3];
            });
            // Apply datatable to the table
            $('#TrabajadoresTable').DataTable();
        });
}

// Fill the becarios table
function getBecarios() {
    var becariosTbody = document.getElementById('BecariosTable').getElementsByTagName('tbody')[0];
    fetch('/list/becarios')
        .then(response => response.json())
        .then(data => {
            data.forEach(becario => {
                // Adding a row to the table
                let row = becariosTbody.insertRow();
                row.insertCell(0).textContent = becario[0];
                row.insertCell(1).textContent = becario[1];
                row.insertCell(2).textContent = becario[2];
            });
            // Apply datatable to the table
            $('#BecariosTable').DataTable();
        });
}

document.addEventListener("DOMContentLoaded", function() {
    // Fill the tables
    getTrabajadores();
    getBecarios();
});
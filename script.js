const apiUrl = "http://localhost:5000"; 

function sendRequest(endpoint, method = 'GET', data = {}) {
    return fetch(`${apiUrl}/${endpoint}`, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: method !== 'GET' ? JSON.stringify(data) : null
    })
    .then(response => response.json())
    .catch(error => console.error('Error:', error));
}

function addPeer() {
    const port = document.getElementById("port").value;
    sendRequest('add_peer', 'POST', { port: port })
        .then(data => {
            document.getElementById("output").innerText = `Peer added on port: ${port}`;
            showNodeButtons();
        });
}

function showNodeButtons() {
    document.getElementById("nodeActions").style.display = "block";
}

function mineBlock() {
    sendRequest('mine', 'POST')
        .then(data => document.getElementById("output").innerText = 'New block mined: ' + JSON.stringify(data));
}

function displayPeers() {
    sendRequest('peers', 'GET')
        .then(data => document.getElementById("output").innerText = 'Connected peers: ' + JSON.stringify(data));
}

function displayBlockchain() {
    sendRequest('blockchain', 'GET')
        .then(data => document.getElementById("output").innerText = 'Blockchain: ' + JSON.stringify(data));
}

function stopServer() {
    sendRequest('stop', 'POST')
        .then(data => document.getElementById("output").innerText = 'Server stopped');
}

document.getElementById("nodeActions").style.display = "none";

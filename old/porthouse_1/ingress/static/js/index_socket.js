var client_id = Date.now()
document.querySelector("#ws-id").textContent = client_id;

var newSocket = function(client_id){
    var ws = new WebSocket(`ws://127.0.0.1:8000/ws/${client_id}`);
    ws.onmessage = function(event) {
        var messages = document.getElementById('messages')
        var message = document.createElement('li')
        var content = document.createTextNode(event.data)
        message.appendChild(content)
        messages.appendChild(message)
        emitEvent(event)
    };
    return ws
}

var emitEvent = function(event) {
    events.emit('socket-message', event)
}

var ws = newSocket(client_id)

function sendMessage(event) {
    var input = document.getElementById("messageText")
    ws.send(input.value)
    input.value = ''
    event.preventDefault()
}


var send = function(text) {
    ws.send(text)
}

$('.buttons .button pre').on('click', function(e){
    send($(this).text())
})

$('button.connect').on('click', function(){
    ws = newSocket(client_id)
})

$('button.copy').on('click', function(){
    $('#messageText').text(($(this).siblings('pre').text()))
})

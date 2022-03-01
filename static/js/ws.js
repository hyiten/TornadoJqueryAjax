function getParameterByName(name, url = window.location.href) {
  name = name.replace(/[\[\]]/g, '\\$&');
  var regex = new RegExp('[?&]' + name + '(=([^&#]*)|&|#|$)'),
    results = regex.exec(url);
  if (!results) return null;
  if (!results[2]) return '';
  return decodeURIComponent(results[2].replace(/\+/g, ' '));
}

function connect() {
  var ws = new WebSocket('ws://localhost:8888/ws/');
  ws.onopen = function () {
    // subscribe to some channels
    // Grab the session id from the url
    sessionkey = getParameterByName('sessionkey');
    ws.send(JSON.stringify({
      //.... some message the I must send when I connect ....
      "session": sessionkey,
      "action": "subscribe",
      "data": ""
    }));
  };

  ws.onmessage = function (e) {
    // process the message
    var jsonData = JSON.parse(e.data);
    //console.log(jsonData);
    if (jsonData.controlCode == 0) {
      console.log('Message:', jsonData);
    } else if (jsonData.controlCode == 1) {
      action = jsonData.data[0].action
      path = jsonData.data[0].path
      location.reload()
    } else if (jsonData.controlCode == 3) {
      action = jsonData.data[0].action
      path = jsonData.data[0].path
      location.reload()
    }
  };

  ws.onclose = function (e) {
    console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
    setTimeout(function () {
      connect();
    }, 1000);
  };

  ws.onerror = function (err) {
    console.error('Socket encountered error: ', err.message, 'Closing socket');
    ws.close();
  };
}
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
    var queryString = window.location.search;
    var urlParams = new URLSearchParams(queryString);
    var sessionkey = urlParams.get("sessionkey");

    if (jsonData.controlCode == 0) {
      console.log('Message:', jsonData);
    } else if (jsonData.controlCode == 1) {
      action = jsonData.data[0].action
      path = jsonData.data[0].path
      //location.reload()
      try {
        var divRoot = document.getElementById("imgRoot")
        var newDiv = document.createElement("div")
        var img = document.createElement("img")
        var filename = path.substring(path.lastIndexOf('/')+1);
        img.src = "/api/loadimage?sessionkey="+sessionkey+"&filename="+filename
        newDiv.id = "imgTable_" + filename.replace(" ","_")
        newDiv.className = "col-md-4 mt-3 col-lg-3"
        img.id = filename
        document.getElementById("imgRoot").appendChild(newDiv)
        var imgTable = document.getElementById("imgTable_" + filename.replace(" ","_"))

        imgTable.appendChild(img)
      } catch (error) {
        console.log(`Error: ${error}`)
      }
    } else if (jsonData.controlCode == 3) {
      action = jsonData.data[0].action
      path = jsonData.data[0].path
      //location.reload()
      try {
        var filename = path.substring(path.lastIndexOf('/')+1);
        var imgTable = document.getElementById("imgTable_" + filename.replace(" ","_"))
        imgTable.remove(imgTable)
      } catch (error) {
        console.log("skipping")
      }
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
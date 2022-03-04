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

    console.log(`incoming data: ${jsonData.data.length} : ${jsonData.data}`);

    for (var i = 0; i < jsonData.data.length; i++) {
      var data = jsonData.data[i];

      //console.log(`in-loop data: ${JSON.stringify(data)}`);
      console.log(`in-loop data: ${data.action}`);

      if (data.action) {
        try {
          action = String(data.action)

          if (action.toUpperCase() == "CHANGE.ADDED") {
            var newDiv = document.createElement("div")
            var img = document.createElement("img")
            var filename = data.path.substring(data.path.lastIndexOf('/') + 1);
            img.src = "/api/loadimage?sessionkey=" + sessionkey + "&filename=" + filename
            newDiv.id = "imgTable_" + filename.replace(" ", "_")
            newDiv.className = "col-md-4 mt-3 col-lg-3"
            img.id = filename
            document.getElementById("imgRoot").appendChild(newDiv)
            var imgTable = document.getElementById("imgTable_" + filename.replace(" ", "_"))

            imgTable.appendChild(img)
          } else if (data.action.toUpperCase() == "CHANGE.DELETED") {
            try {
              var filename = data.path.substring(data.path.lastIndexOf('/') + 1);
              var imgTable = document.getElementById("imgTable_" + filename.replace(" ", "_"))
              imgTable.remove(imgTable)
            } catch (error) {
              console.log("skipping")
            }

          }
        } catch (error) {
          console.log(`Error: ${error}`)
        }
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
 $(document).ready(function() {
    namespace = '/test';
    var myName = window.current_user_name;
    if (myName){
        var socket = io.connect('http://' + document.domain + ':' + location.port + namespace);

        socket.on('connect', function () {
            socket.emit('user_connected', {data: myName+' connected!'});

        });

        if (window.started) {
            socket.emit('start_game');
        }
    }

    //get opposing players from JSON message with player property of json
    function getOpposingPlayers(blob){
        var opposingPlayers = JSON.parse(blob).data.players;
        delete opposingPlayers[myName];
        for (var player in opposingPlayers){
            delete opposingPlayers[player].hand;
        }
        return opposingPlayers;
    }

    //helper function to parse JSON received from server
    function getMyData(blob){
        var myData = JSON.parse(blob).data.players[myName];
        return myData;
    }

    // send chat
    $('form#broadcast').submit(function(event) {
        socket.emit('send_chat', {data: myName + " says: " + $('#broadcast_data').val()});
        return false;
    });

    $('form#startgame').submit(function(event) {
        socket.emit('start_game');
        return false;
    });

    // event handler for server sent data
    // the data is displayed in the "Received" section of the page
    socket.on('my response', function(msg) {
        $('#log').append('<br>' + msg.data);
    });

    socket.on('start_game', function(msg){
        $('#log').append('<br>' + msg.data.log);
        playerData = msg.data.players;
        players = [];
        for(var player in playerData) {
           players.push(playerData[player]);
        }
        $('#players').empty();
        for(var i = 0; i < players.length; i++){
            $('#players').append(
                '<div id=' + players[i].name + '><div class=\'tricks_taken\'></div><div class=\'bid\'></div></div>');
        }
    });

    socket.on('refresh', function(msg){
        opposingPlayers = getOpposingPlayers(msg);
        myData = getMyData(msg);
    });

    //redirect event listener - data should be 'url': url_for('redirect_page')
    socket.on('redirect', function (data) {
        window.location = data.url;
    });
});
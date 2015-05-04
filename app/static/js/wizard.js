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

    socket.on('request_name', function(msg) {
        socket.emit('send_name', {data: myName})
    });

    socket.on('start_game', function(msg){
        console.log(msg);
        $('#log').append('<br>' + msg.data.log);
        var players = msg.data.players;


        $('#players').empty();
        for(var i = 0; i < players.length; i++){
            $('#players').append(
                '<div id=' + players[i] + '><p>'+ players[i] +'<br></p>Taken:<br><div class=\'tricks_taken\'></div>Bid:<br><div class=\'bid\'></div></div>');
            $('#scorecard').append(
                '<div id=' + (players[i] + "score") + '><p>'+ players[i] +'<br></p><div class=\'scround\'>R<br></div><div class=\'sctrickstaken\'>T<br></div><div class=\'scbid\'>B<br></div><div class="score">S<br></div></div>');
        }
    });

    socket.on('refresh', function(msg){
        var players = msg.data.players;
        var gameData = msg.data.game;
        console.log(players)
        console.log(gameData)
    });

    //redirect event listener - data should be 'url': url_for('redirect_page')
    socket.on('redirect', function (data) {
        window.location = data.url;
    });
});
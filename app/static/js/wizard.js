 $(document).ready(function() {
    namespace = '/test';
    var myName = window.current_user_name;

    window.setInterval(function() {
      var elem = document.getElementById('log');
      elem.scrollTop = elem.scrollHeight;
    }, 1000);

    function decodeScores(score) {
        result = score.split('.');
        for (var i = 0; i < result.length; i++ ) {
            holder = result[i].split(',');
            result[i] = holder;
        }
        return result;
    }

    if (myName){
        var socket = io.connect('http://' + document.domain + ':' + location.port + namespace);

        socket.on('connect', function () {
            socket.emit('user_connected', {data: myName});
        });

        if (window.started) {
            socket.emit('start_game');
        }
    }

    // send chat
    $('form#broadcast').submit(function(event) {
        socket.emit('send_chat', {data: myName + " says: " + $('#broadcast_data').val()});
        $('#broadcast')[0].reset();
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

    socket.on('user_connect_message', function(msg) {
        $('#log').append('<br>' + msg.data + " connected!");
    });
    socket.on('start_game', function(msg){
        $('#log').append('<br>' + msg.data.log);

        var players = msg.data.scores;

        $('#players, #scorecard').empty();
        for(var i = 0; i < players.length; i++){
            $('#players').append('<div class="playerspace"><div>'+ players[i] +'</div><div class=\'dealer\'>dealer</div><br>Taken: <div class=\'tricks_taken\'></div><div class=\'turn\'>turn</div><br>Bid: <div class=\'bid\'></div><br>Hand:<br><div class=\'hand\'></div></div>');
            $('#scorecard').append("<div class='score'><p>"+ players[i] +"<br></p><div class='scoreheader'><div class=\'scround\'>R<br></div><div class=\'sctrickstaken\'>T<br></div><div class=\'scbid\'>B<br></div><div class=\'scscore\'>S<br></div></div></div>");
        }

        $('.score').each(function() {
            for (var i = 1; i < numOfRounds + 1; i++) {
                $(this).append("<div class='scorerow' data-row=" + i + "><div class=\'scround\'>" + i +"<br></div><div class=\'sctrickstaken\'><br></div><div class=\'scbid\'><br></div><div class=scscore><br></div></div>");
            }
        });
    });

    socket.on('start', function(msg) {
        var scores = msg.data.scores;
        var gameData = msg.data.game;
        var dealer = (gameData.round % 4) - 1;
        var turn = gameData.turn;

        $('.dealer').each(function (i) {
            $(this).hide();
            if (i == dealer) {
                $(this).show();
            }
        });

        $('#round').html(gameData['round']);

        $('.score').each(function( i ){
           $(this).find('.scorerow').each(function( j ){
               if(typeof scores[i].score[j] != 'undefined') {
                   $(this).find('.sctrickstaken').html(scores[i].score[j][0]);
                   $(this).find('.scbid').html(scores[i].score[j][1]);
                   $(this).find('.scscore').html(scores[i].score[j][2]);
               }
           });
        });

        $('.playerspace').each(function( i ) {
            $(this).find('.tricks_taken').html(scores[i].score[gameData['round'] - 1][0]);
            $(this).find('.bid').html(scores[i].score[gameData['round'] - 1][1]);

            var hand = scores[i].score[gameData['round'] - 1][3].split(' ');
            for (var j = 0; j < hand.length; j++) {
                $(this).find('.hand').append("<div>" + hand[j] + "</div>");
            }

            if ( i == turn) {
                $('.turn').hide();
                $(this).find('.turn').show();
                $(this).find('.turn').css("background-color", "yellow");
            }
        });
    });

    socket.on('refresh', function(msg) {
        var scores = msg.data.scores;
        var gameData = msg.data.game;
        var dealer = (gameData.round % 4) - 1;
        var turn = gameData.turn;

        $('.dealer').each(function (i) {
            $(this).hide();
            if (i == dealer) {
                $(this).show();
            }

        });

        $('#round').html(gameData['round']);

        $('.score').each(function( i ){
            $(this).find('.scorerow').each(function( j ){
               if(typeof scores[i].score[j] != 'undefined') {
                   $(this).find('.sctrickstaken').html(scores[i].score[j][0]);
                   $(this).find('.scbid').html(scores[i].score[j][1]);
                   $(this).find('.scscore').html(scores[i].score[j][2]);
               }
           });
        });

        $('.playerspace').each(function( i ) {
            $(this).find('.tricks_taken').html(scores[i].score[gameData['round'] - 1][0]);
            $(this).find('.bid').html(scores[i].score[gameData['round'] - 1][1]);

            if ( i == turn) {
                $('.turn').hide();
                $(this).find('.turn').show();
                $(this).find('.turn').css("background-color", "yellow");
            }
        });

        $('#played').append(gameData['played_cards']);
    });

    socket.on('server_message', function(msg) {
        $('#log').append('<br>' + msg.data)
    });

    socket.on('your_bid', function(msg){
        bidSpace = $($(".bid").get(msg.data.turntobid));
        bidSpace.empty();

        for (var i = 0; i < msg.data.rdnumber + 1; i++){
            bidSpace.append("<div>&nbsp;" + i + "&nbsp;</div>");
        }
        $(bidSpace.find('div')).click(function(){
            var bid = $(this).html().slice(6,7);
            socket.emit('bidcast', {
                'data': {
                    'bid': bid,
                    'bidder': msg.data.bidder
                }
            });
            $(bidSpace.find('div')).off('click');

        });
    });

    socket.on('your_turn', function(msg) {
        $($(".hand").get(msg.data)).css( 'cursor', 'hand');
        $($(".hand").get(msg.data)).children().on('click', function(){
            var card = $(this).html();
            $(this).hide();
            socket.emit('cardplayed', {'data': card} );
            $('.hand div').off('click');
        });
    });

    //shows everyone whose bid it is
    socket.on('bidder', function(msg) {
        $('.bid').removeClass('bidding');
        $($('.bid').get(msg.data.turntobid)).addClass('bidding' );
    });

    socket.on('redirect', function (data) {
        window.location = data.url
    });
});
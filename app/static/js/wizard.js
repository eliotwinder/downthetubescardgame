 $(document).ready(function() {
    var namespace = '/test';
    var myName = window.current_user_name;
    var number_of_players = 2

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
            $('#players').append('<div class="playerspace"><div>'+ players[i] +'</div><div class=\'dealer\'>dealer</div><br>Taken: <div class=\'tricks_taken\'></div><div class=\'turn\'>turn</div><br>Bid: <div class=\'bid\'></div><div class=\'go\'>GO!!</div><br>Hand:<br><div class=\'hand\'></div></div>');
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
        var dealer = (gameData.round % number_of_players) - 1;
        var turn = gameData.turn;
        var trump = gameData.trump;

        $('#trump').html(trump);

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
                $(this).find('.hand').empty()
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

        $('#played').empty();
        $('#played').append(gameData['played_cards']);
    });

    socket.on('server_message', function(msg) {
        $('#log').append('<br>' + msg.data)
    });

    socket.on('choose_trump', function(){
        $('#choosetrump').show();
        $('#choosetrump div').click(function() {
            socket.emit('trump_chosen', {'data': {'trump': $(this).html(), 'chooser': myName}});
            $('#choosetrump').hide();
        })
    });

    socket.on('trump_chosen', function(msg){
        $("#trump").append("--> " + msg['trump']);
    });

    socket.on('your_bid', function(msg){

        bidSpace = $($(".bid").get(msg.data.turntobid));
        bidSpace.empty();

        var totalBid = 0;
        $($(".go").get(msg.data.turntobid)).show();
        $('.bid').each(function(i){
           if ( i != msg.data.turntobid) {
               totalBid += $(this).html();
           }
        });



        for (var i = 0; i < msg.data.rdnumber + 1; i++) {
            if (msg.data.bidder != msg.data.rdnumber) {
                console.log();
                bidSpace.append("<div>&nbsp;" + i + "&nbsp;</div>");
            } else {
                console.log('here');
                if (i != Math.abs(totalBid - msg.data.rdnumber)) {
                    bidSpace.append("<div>&nbsp;" + i + "&nbsp;</div>");
                }
            }
        }
        console.log(msg);
        $(bidSpace.find('div')).click(function(){
            var bid = $(this).html().slice(6,7);
            $(".go").hide();
            socket.emit('bidcast', {
                'data': {
                    'bid': bid,
                    'bidder': msg.data.bidder
                }
            });
            $($(".go").get(msg.data)).show();
            $('.bid').removeClass('bidding');
            $(bidSpace.find('div')).off('click');

        });
    });

    //shows everyone whose bid it is
    socket.on('bidder', function(msg) {
        $('.bid').removeClass('bidding');
        $($('.bid').get(msg.data.turntobid)).addClass('bidding' );
    });

    socket.on('bidding_over', function(){
        $('.bid').removeClass('bidding');
    });

    socket.on('your_turn', function(msg) {
        $($(".go").get(msg.data)).show();
        $($(".hand").get(msg.data)).css( 'cursor', 'hand');
        $($(".hand").get(msg.data)).css( 'background-color', 'red');
        $($(".hand").get(msg.data)).css( 'color', 'white');
        $($(".hand").get(msg.data)).children().on('click', function(){
            var card = $(this).html();
            $(this).hide();
            socket.emit('cardplayed', {'data': card} );
            $('.hand div').off('click');
            $($(".go").get(msg.data)).hide();
        });
    });



    socket.on('redirect', function (data) {
        window.location = data.url
    });
});
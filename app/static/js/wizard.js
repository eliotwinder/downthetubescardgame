 $(document).ready(function() {
    var namespace = '/test';
    var myName = window.current_user_name;
    var numberOfPlayers = 2;

    window.setInterval(function() {
      var elem = document.getElementById('log');
      elem.scrollTop = elem.scrollHeight;
    }, 1000);

    function decodeScores(score) {
        console.log(score);
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

    // start a game!
    $('form#startgame').submit(function(event) {
        socket.emit('start_game');
        return false;
    });

    // event handler for server sent messages
    // the data is displayed in the "Received" section of the page
    socket.on('server_message', function(msg) {
        $('#log').append('<br>' + msg.message)
    });

    //TODO: is this neccesary? same as server_message?
    socket.on('my response', function(msg) {
        $('#log').append('<br>' + msg.data);
    });

    //notify that someone is connected
    socket.on('user_connect_message', function(msg) {
        $('#log').append('<br>' + msg.data + " connected!");
    });

    //set the screen for new game msg = logMessage: message to log, rounds: rounds
    socket.on('start_game', function(msg){
        //log that the game has started
        $('#log').append('<br>' + msg.logMessage);

        //get rounds
        var scoresheets = msg.rounds;

        //empty out the playing field
        $('#players, #scorecard').empty();

        //for each scoresheet
        for(var i = 0; i < scoresheets.length; i++){

            //add a playerspace TODO: better way to do this with templates?
            $('#players').append(
                '<div id=' + scoresheets[i][player] +'class="playerspace">' +
                    '<span class=\'playerspacename\'>' + players[i] + '</span>' +
                    '<span>Taken:</span>' +
                    '<div class=\'tricks_taken\'></div><br>' +
                    'Bid: <div class=\'bid\'></div>' +

                    '<div id=\'notifications\'>' +
                        '<div class=\'dealer\'>dealer</div><br>' +
                        '<div class=\'turn\'>turn</div>' +
                        '<div class=\'go\'>GO!!</div><br>' +
                    '<div class=\'hand\'>,' +
                    '   <span> Hand:<br></span>' +  //will be filled with card divs
                    '</div>' +
                '</div>');

            //build scorecard
            $('#scorecard').append(
                    "<div class='score>'"+ players[i] +"<br>" +
                        "<div class='scoreheader'>" +
                            "<div class=\'scround\'>R</div><br>" +
                            "<div class=\'sctrickstaken\'>T<br></div>" +
                            "<div class=\'scbid\'>B</div><br>" +
                            "<div class=\'scscore\'>S<br></div>" +
                        "</div>" +
                     "</div>");
        }

        //add a row for each round
        $('.score').each(function() {
            for (var i = 1; i < numOfRounds + 1; i++) {
                $(this).append(
                        "<div class='scorerow' data-row=" + i + ">" +
                            "<div class=\'scround\'>" + i +"</div><br>" +
                            "<div class=\'sctrickstaken\'></div><br>" +
                            "<div class=\'scbid\'></div><br>" +
                            "<div class=\'scscore\'><br></div>" +
                        "</div>");
            }
        });
    });

    socket.on('start', function(msg) {
        var scores = msg.data.scores;
        var gameData = msg.data.game;
        var dealer = (gameData.round % numberOfPlayers) - 1;
        var turn = gameData.turn;
        var trump = gameData.trump;

        $('#trump').html(trump);

        $('#played').empty();

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

            var hand = scores[i]['score'][gameData['round'] - 1][3].split(" ");

            for (var j = 0; j < hand.length; j++) {
                $(this).find('.hand').empty();
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



    socket.on('choose_trump', function(){
        //show the choose a trump panel
        $('#choosetrump').show();

        //event listener to tell the server what player chose and close the choose trump panel
        $('#choosetrump div').click(function() {
            socket.emit('trump_chosen', {'data': {'trump': $(this).html(), 'chooser': myName}});
            $('#choosetrump').hide();
        })
    });

    //receive new trump
    socket.on('trump_chosen', function(msg){
        $("#trump").append("--> " + msg['trump']);
    });

    //shows everyone whose bid it is
    socket.on('new_bidder', function(bidIndex) {
        $('.bid').removeClass('bidding');
        $($('.bid').get(bidIndex)).addClass('bidding' );
    });

    //receive a request to bid along with data.roundNumber, data.bidIndex and data.totalBid
     socket.on('your_bid', function(data) {
         var roundNumber = data.roundNumber
         var bidderIndex = data.bidderIndex;
         var totalBid = data.totalBid;

         // selects the bid display div for the current bidder and clears it to make way for the buttons
         var biddersSpace = $($(".bid").get(bidderIndex));
         biddersSpace.empty();

         //show the GO!! alert
         $($(".go").get(bidderIndex)).show();

         //if you're the last to deal, only show your possible bids
         if (bidderIndex == numberOfPlayers) {
             for (var i = 0; i < roundNumber + 1; i++) {
                 //check if you can bid each # - if you can, add the div
                 if ( i != totalBid + roundNumber) {
                     biddersSpace.append('<div class=\'bidselect\'>' + i + '</div>');
                 }
             }
         //if you're not the last to bid, display all possible bids
         } else {
             for (var i = 0; i < roundNumber + 1; i++) {
                 biddersSpace.append('<div class=\'bidselect\'>' + i + '</div>');
             }
         }

        //add event listener to send bid
        $('.bidselect').click(function(){
            var bid = $(this).html();
            $(".go").hide();

            //tell the server your bid
            socket.emit('bid_cast', bid);

            // remove event listener and change bid to selected bid
            $(biddersSpace).html(bid);
            $(biddersSpace.find('div')).off('click');
        });
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

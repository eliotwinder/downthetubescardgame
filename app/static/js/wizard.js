$(document).ready(function () {
    var namespace = '/test';
    var myName = window.current_user_name;
    var numberOfPlayers = 2;

    window.setInterval(function () {
        var elem = document.getElementById('log');
        elem.scrollTop = elem.scrollHeight;
    }, 1000);

    if (myName) {
        var socket = io.connect('http://' + document.domain + ':' + location.port + namespace);

        socket.on('connect', function () {
            socket.emit('user_connected', {data: myName});
        });

        if (window.started) {
            socket.emit('start_game');
        }
    }

    //notify that someone is connected
    socket.on('user_connect_message', function (msg) {
        $('#log').append('<br>' + msg.data + " connected!");
    });

    socket.on('redirect', function (data) {
        window.location = data.url
    });

    // send chat
    $('form#broadcast').submit(function (event) {
        socket.emit('send_chat', {data: myName + " says: " + $('#broadcast_data').val()});
        $('#broadcast')[0].reset();
        return false;
    });

    // event handler for server sent messages
    // the data is displayed in the "Received" section of the page
    socket.on('server_message', function (msg) {
        $('#log').append('<br>' + msg.message)
    });

    // start a game!
    $('form#startgame').submit(function (event) {
        socket.emit('start_game');
        return false;
    });

    //set the screen for new game msg = logMessage: message to log, rounds: rounds
    socket.on('start_game', function (msg) {
        //log that the game has started
        $('#log').append('<br>' + msg.logMessage);

        //get rounds
        var players = msg.players;

        //empty out the playing field
        $('#players, #scorecard').empty();

        //for each scoresheet
        for (var i = 0; i < players.length; i++) {

            //add a playerspace TODO: better way to do this with templates?
            $('#players').append(
                    '<div id' + players[i] + '\' class="playerspace">' +
                    '<div class=\'currentstats\'>' +
                        '<span class=\'playerspacename\'>' + players[i] + '</span><br>' +
                        '<span>Taken:</span>' +
                        '<div class=\'trickstaken\'></div><br>' +
                        '<span>Bid:</span>' +
                        '<div class=\'bid\'></div><br>' +

                        '<span> Hand:<br></span>' +
                        '<div class=\'hand\'></div>' +
                    '</div>' +

                    '<div class=\'notifications\'>' +
                        '<div class=\'dealer\'>dealer</div><br>' +
                        '<div class=\'turn\'>turn</div>' +
                        '<div class=\'go\'>GO!!</div><br>' +
                    '</div>' +
                    '</div>');

            //build scorecard
            $('#scorecard').append(
                    "<div class='score'>" + players[i] + "<br>" +
                    "<div class='scoreheader'>" +
                    "<div class='scround'>R</div><br>" +
                    "<div class='sctrickstaken'>T<br></div>" +
                    "<div class='scbid'>B</div><br>" +
                    "<div class='scscore'>S<br></div>" +
                    "</div>" +
                    "</div>");
        }

        //add a row for each round
        $('.score').each(function () {
            for (var i = 1; i < numOfRounds + 1; i++) {
                $(this).append(
                        "<div class='scorerow'>" +
                            "<div class='scround'>" + i + "</div><br>" +
                            "<div class='sctrickstaken'></div><br>" +
                            "<div class='scbid'></div><br>" +
                            "<div class='scscore'><br></div>" +
                        "</div>");
            }
        });
    });

    // reset round div
    socket.on('update_round', function (msg) {
        $('#round').html(msg.round);
    });

    // show your hand
    socket.on('deal_hand', function (msg) {
        var hand = JSON.parse(msg.hand);
        console.log(Array.isArray(hand));
        for (var i = 0; i < hand.length; i++) {
            $(myName + ' .hand').append(msg.hand[i]);
        }
    });

//    let
    socket.on('pass_trump', function(msg) {
        $('#trump').html(msg.trump);
    });

    // tells you to choose trump
    socket.on('choose_trump', function () {
        //show the choose a trump panel
        $('#choosetrump').show();

        //event listener to tell the server what player chose and close the choose trump panel
        $('#choosetrump div').click(function () {
            socket.emit('trump_chosen', {'data': {'trump': $(this).html(), 'chooser': myName}});
            $('#choosetrump').hide();
        })
    });

    //receive new trump
    socket.on('trump_chosen', function (msg) {
        $("#trump").append("--> " + msg['trump']);
    });

    //shows everyone whose bid it is
    socket.on('new_bidder', function (msg) {
        $('.bid').removeClass('bidding');
        $($('.bid').get(msg.bidderIndex)).addClass('bidding');
    });

    //receive a request to bid along with data.roundNumber, data.bidIndex and data.totalBid
    socket.on('your_bid', function (data) {
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
                if (i != totalBid + roundNumber) {
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
        $('.bidselect').click(function () {
            var bid = $(this).html();
            $(".go").hide();

            //tell the server your bid
            socket.emit('bid_cast', bid);

            // remove event listener and change bid to selected bid
            $(biddersSpace).html(bid);
            $(biddersSpace.find('div')).off('click');
        });
    });

    //bidding is finished, remove highlight on bidding
    socket.on('bidding_over', function () {
        $('.bid').removeClass('bidding');
    });

    //refresh bid
    socket.on('refresh_bid', function (msg) {
        $('.bid').each(function (i) {
            $(this).html(msg.bidArray[i]);
        });
    });

    //server requests a played card
    socket.on('your_turn', function (msg) {
        $(myName + " .go").show();
        var myHand = $(myName + " .hand");
        myHand.addClass('playing');

        myHand.children().on('click', function () {
            var card = $(this).html();
            $(this).hide();
            $('.hand div').off('click');
            $(myName + " .go").show();
            socket.emit('card_played', {'card': card});
        });
    });

    //refresh tricks taken
    socket.on('refresh_tricks_taken', function (msg) {
        $('.trickstaken').each(function (i) {
            $(this).html(msg.tricksTaken[i]);
        });
    });

    socket.on('update_scorecard', function(msg){
        gameRound = msg.gameRound;
        stats = msg.statsArray  // array of round objects in order of player position

        $('.score > .scorerow:nth-of-type(game.round)').each(function(i) {
           $(this).find('.sctrickstaken').html(stats[i].tricks_taken);
           $(this).find('.scbid').html(stats[i].bid);
           $(this).find('.scscore').html(stats[i].score);
        });
    });
});



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

        //empty out the playing field
        $('#opponents, #quickscore, .user, #scorecard').empty();

        //get players
        var players = msg.players;
        var myIndex = players.indexOf(myName);

        for (var i = 0; i < players.length; i++) {
            //build scorecard
            $('#scorecard').append(
                    "<div class='score'>" + players[i] + "<br>" +
                    "<div class='scoreheader'>" +
                    "<div class='scround'>R</div>" +
                    "<div class='sctrickstaken'>T</div>" +
                    "<div class='scbid'>B</div>" +
                    "<div class='scscore'>S</div>" +
                    "</div>" +
                    "</div>"
            );

            //build quickscore
            $('#quickscore').append(
                    "<div class='quickscoreplayer'>" +
                    "<div class='quickscorename'>" + players[i] + "</div><br>" +
                    "<div class='quickscorenumber'>0</div>" +
                    "</div>"
            );
        }

        //add a row for each round
        $('.score').each(function () {
            for (var i = 1; i < (60/numberOfPlayers) + 1; i++) {
                $(this).append(
                    "<div class='scorerow round"+ i +"'>" +
                        "<div class='scround'>" + i + "</div>" +
                        "<div class='sctrickstaken'></div>" +
                        "<div class='scbid'></div>" +
                        "<div class='scscore'></div>" +
                    "</div><br>"
                );
            }
        });

        //reorder players so this player is last
        for (var i = 0; i < myIndex; i++) {
            players.push(players.shift());
        }

        //for each scoresheet
        for (var i = 0; i < players.length; i++) {
            //add a playerspace TODO: better way to do this with templates?
            if (i !== 0) {
                $('#opponents').append(
                        '<div id=\'' + players[i] + '\' class="playerspace">' +
                        '<div class=\'playerspacename\'>' + players[i] + '</div>' +
                        '<div class=\'dealer\' dispay=\'none\'>D </div><br>' +
                        '<div class=\'subheading\'>won</div>' +
                        '<div class=\'trickstaken\'>0</div>' +
                        '<div> / </div>' +
                        '<div class=\'bid\'>0</div>' +
                        '<div class=\'subheading\'>bid</div>' +
                        '<br>' +
                        '<div class=\'playedcard\'></div>' +
                        '</div>');
            } else {
                //add user
                $('.user').append(
                        '<div id=\'' + players[0] + '\' class="playerspace">' +
                        '<div class="playedcard"></div>' +
                        '<div class="hand"></div>' +
                        '<div class=\'playerspacename\'>' + players[0] + '</div>' +
                        '<div class=\'dealer\' dispay=\'none\'>D </div><br>' +
                        '<div class=\'subheading\'>won</div>' +
                        '<div class=\'trickstaken\'>0</div>' +
                        '<div> / </div>' +
                        '<div class=\'bid\'>0</div>' +
                        '<div class=\'subheading\'> bid</div>' +
                        '<br>' +
                        '<div>'
                );
            }
        }
    });

    // reset round div
    socket.on('update_round_and_dealer', function (msg) {
        var dealerName = msg.dealer;
        $('#showround').html(msg.round);
        $('.dealer').hide();
        $('#' + dealerName).find('.dealer').show();
    });

    function createCard(suit, rank) {
        var card = document.createElement('div');
        card = $(card);
        card.addClass('card');
        card.addClass(suit);
        card.addClass(rank);
        card.append("<div class='rank'>" + rank + "</div><div class='suit'>" + suit + "</div>");
        card.css('background-image', 'url("static/images/' + suit + '/' + rank +'.png")');
        return card;
    }


    // show your hand
    //TODO: data is coming in a string but we need an array. i've written a function - better way to do this?
    socket.on('deal_hand', function (msg) {
        var h = msg.hand;
        console.log(h);
        for (var i = 0; i < h.length; i++) {
            $("#" + myName).find(".hand").append(
                createCard(h[i].suit , h[i].rank )
            );
        }
    });

    // add trump card to the trump div
    socket.on('pass_trump', function(msg) {
        $('#showtrump').html(createCard(msg.trump.suit, msg.trump.rank));
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
        $("#trump").append(" " +msg['trump']);
    });

    //shows everyone whose bid it is
    socket.on('new_bidder', function (msg) {
        $('.playerspace').removeClass('bidding');
        $('#' + msg.bidder).addClass('bidding');
    });

    //receive a request to bid along with data.roundNumber, data.bidIndex and data.totalBid
    socket.on('your_bid', function (data) {
        var roundNumber = data.roundNumber
        var totalBid = data.totalBid;
        var lastBidder = data.lastBidder

        // selects the bid display div for the current bidder and clears it to make way for the buttons
        var biddersSpace = $("#bid");
        biddersSpace.empty();

        //if you're the last to deal, only show your possible bids
        if (lastBidder === 'true') {
            for (var i = 0; i < roundNumber + 1; i++) {
                //check if you can bid each # - if you can, add the div
                if (i + totalBid != roundNumber) {
                    biddersSpace.append('<div class=\'bidselect\'>' + i + '</div>');
                }
            }
        //if you're not the last to bid, display all possible bids
        } else {
            for (var i = 0; i < roundNumber + 1; i++) {
                biddersSpace.append('<div class=\'bidselect\'>' + i + '</div>');
            }
        }

        $('#bidarea').show();

        //add event listener to send bid
        $('.bidselect').click(function () {
            var bid = $(this).html();
            $('#bidarea').hide();

            //tell the server your bid
            socket.emit('bid_cast', {'bid': bid});

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
        $('#' + msg.bidder).find('.bid').text(msg.bidAmount);
    });


    //server requests a played card
    socket.on('your_turn', function (msg) {
        var myHand = $("#" + myName + " .hand");
        myHand.addClass('playing');
        var ledSuit = msg.ledSuit;

        //check if the player has this suit and must follow
        var hasLedSuit = false;
        myHand.children().each(function(){
            if ($(this).hasClass(ledSuit)) {
                hasLedSuit = true
            }
        });

        //if player has to follow, make it so they can't click the cards they can't play
        if (hasLedSuit) {
            myHand.children().each(function () {
                var canPlayCard = false;
                if ([ledSuit, "W", "J"].indexOf($(this).find('.suit').text()) > -1) {
                    canPlayCard = true;
                }
                if (canPlayCard) {
                    $(this).click(function () {
                        var card = $(this).text();
                        $('.hand div').off('click');
                        myHand.removeClass('playing');
                        $(this).remove();
                        socket.emit('card_played', {'card': card});
                    });
                } else {
                    $(this).click(function(){
                        alert("You gots to follow the led suit!!!")
                    });
                }
            });
        } else {
            myHand.children().each(function () {
                $(this).click(function () {
                    var card = $(this).text();
                    $('.hand div').off('click');
                    myHand.removeClass('playing');
                    $(this).remove();
                    socket.emit('card_played', {'card': card});
                });
            });
        }
    });

    socket.on('new_turn', function(msg) {
        $('.playerspace').removeClass('bidding');
        $("#" + msg.player).addClass('bidding');
    });

    socket.on('card_played', function(msg) {
         $("#" + msg.player).find(".playedcard").append(
            "<div class='card " + msg.rank + " " + msg.suit +"'>" +
                "<div class='rank'>" + msg.rank + "</div>" +
                "<div class='suit'>" + msg.suit + "</div>" +
            "</div>"
         );
    });

    //refresh tricks taken
    socket.on('refresh_tricks_taken', function (msg) {
        $('.playedcard').empty();
        var players = msg.players;
        var tricksTaken = msg.tricksTaken;
        for (var i = 0; i < players.length; i ++){
            $('#' + players[i]).find('.trickstaken').text(tricksTaken[i]);
        }
    });

    socket.on('update_scorecard', function(msg){
        gameRound = msg.gameRound;

        stats = msg.stats;  // array of round objects in order of player position
        $('.round' + gameRound).each(function(i) {
           $(this).find('.sctrickstaken').html(stats[i].tricks_taken);
           $(this).find('.scbid').html(stats[i].bid);
           $(this).find('.scscore').html(stats[i].score);
        });

        $('.quickscorenumber').each(function(i) {
            $(this).html(stats[i].score);
        });
    });

    //scoreboard popout
    $('#quickscorecontainer').click(function(){
      $('#scorecard').show();
    });

    $('#scorecard').click(function(){
        $('#scorecard').hide();
    });
});



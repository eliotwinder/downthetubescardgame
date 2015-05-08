from app import db, socketio
import json, random, views
from flask.ext.login import current_user
from random import shuffle
from sqlalchemy import desc
from flask import redirect, url_for, jsonify
from flask.ext.socketio import SocketIO, emit, send, join_room, leave_room, close_room, disconnect



# ###  A WORD ABOUT NOMENCLATURE  ####
# scoresheet = row in score table, which includes player, game, rounds, position
# rounds is a list of objects that are each a round - index 0 is rd one, index 2 is rd two, etc.
# round = {
# tricks_taken,
#    bid,
#    round_score
#    hand


# [0: { tricks_taken: this_round's_tricks_taken, bid: this_round's_bid, round_score: round_score, hand: [[suit, number], card, card, card}, <--#rd1
#                      1: { this_round's_tricks_taken, bid: this_round's_bid, round_score, hand}, <--#rd2
#                       { this_round's_tricks_taken, bid: this_round's_bid, round_score, hand}, <--#rd3
#
# cards = two item list [suit, number]
# hand = a list of cards [[H,12],[W,00],etc.]
#
#
# game_info = a row in the game table with round, turn, trick_counter, game_started/ended, trump. .scores gets associated rows from the scores table

namespace = "/test"
number_of_players = 2  # TODO: make these properties of Game
number_of_rounds = 4


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round = db.Column(db.Integer, default=0)
    turn = db.Column(db.Integer, default=0)  # index for who will play a card next
    bid_index = db.Column(db.Integer, default=0)
    trick_counter = db.Column(db.Integer, default=0)
    player_count = db.Column(db.Integer, default=0)
    game_started = db.Column(db.Boolean, default=False)
    time_started = db.Column(db.DateTime)
    game_ended = db.Column(db.Boolean, default=False)
    # list of cards(which are lists) *count length of these to see if trick is over
    trump = db.Column(db.String)
    scores = db.relationship('Score', backref='games', lazy='dynamic')

    def __repr__(self):
        return "game# %r" % str(self.id)

    # returns the latest game
    @classmethod
    def get_game(cls):
        game = cls.query.order_by('id desc').first()
        return game

    #returns a list pointing to scoresheets for a given round in order of position
    def get_scoresheets(self):
        scoresheets = self.scores.order_by('position desc').all()
        scoresheets.reverse()
        return scoresheets

    # returns a list of players name's in order of position
    def get_players(self):
        return [scoresheet.player for scoresheet in Game.get_game().get_scoresheets()]

    # returns the index of the nth bidder for this round
    def get_bidder_index(self):
        return (self.round + self.bid_index) % number_of_players

    def get_bidder_name(self):
        game = self.get_game()
        scoresheets = game.get_scoresheets()
        bidder_index = game.get_bidder_index()
        bidder_name = scoresheets[bidder_index].player
        return bidder_name

    def get_turn_index(self):
        return (self.round + self.turn) % number_of_players

    def get_turn_name(self):
        game = self.get_game()
        scoresheets = game.get_scoresheets()
        turn_index = game.get_turn_index()
        turn_name = scoresheets[turn_index].player
        return turn_name

    def get_total_bid(self):
        game = self.get_game()
        scoresheets = game.get_scoresheets()
        return reduce(lambda x, y: x.get_bid_by_round(game.round) + y.get_bid_by_round(game.round), scoresheets)

    # return a list of the cards played in a given trick and round
    def get_played_cards(self, round, trick):
        scoresheets = self.get_scoresheets()
        return [scoresheet.played_cards[round][trick] for scoresheet in scoresheets]

    # return trump given round
    def get_trump(self, round):
        return self.trump[round]

    @classmethod
    def create_game(cls):
        #create row in game table
        game = Game(game_started=True)
        db.session.add(game)
        db.session.commit()

        #randonly assing order that will be assigned when we create scoresheets
        positions = range(0, number_of_players)
        random.shuffle(positions)

        #create a scoresheet for each player
        for player in range(number_of_players):
            p = Scoresheet(player=player.name, game=game.id, position=positions.pop(), score="")
            db.session.add(p)
        db.session.commit()

        #select the newly created scoresheets
        scoresheets = game.get_scoresheets()

        #select the rounds for each scoresheet -->
        # [[list(player0rounds)],[list(player1rounds)]
        rounds = [scoresheet.get_round() for scoresheet in scoresheets]

        # assemble data to be sent
        send_data = {
            'logMessage': 'game started',
            'rounds': rounds
        }

        socketio.emit('start_game',
                      send_data,
                      namespace=namespace)

        #play the first round
        game.play_round()


    @classmethod
    def play_round(cls):
        #select game and scoresheets
        game = cls.get_game()
        scoresheets = game.get_scoresheets()

        #check if the game is over
        if game.round == number_of_rounds:
            print "game over!"
            return

        # increase round counter - round is 1 indexed - 1 == rd1
        game.round += 1
        # set who's turn it is to index 1 (dealer is index 0, so it's left of the dealer)
        game.turn = game.round

        #add round to score and played cards in the database
        for scoresheet in scoresheets:
            scoresheet.rounds.append([])
            scoresheet.played_cards.append([])
        db.session.commit()

        # let everyone know the round started through a server message
        socketio.emit('server_message', {'message': 'Round' + str(game.round) + "...FIGHT!!!"}, namespace=namespace)
        socketio.emit('update_round', {'round': game.round}, namespace=namespace)

        # shuffle up n deal
        Game.deal()


    @classmethod
    def deal(cls):
        game = cls.get_game()
        scoresheets = game.get_scoresheets()

        # build the deck
        deck = []
        suits = ['C', 'D', 'H', 'S']
        for suit in suits:
            for i in range(1, 14):
                deck.append([suit, i])  # TODO: will this append a list, or add these two items to the list
        for i in range(3):
            deck.append(["W", 27])
            deck.append(["J", 0])

        #shuffle
        shuffle(deck)

        # deal the cards
        for scoresheet in scoresheets:
            # select the hand from scoresheet object
            round = scoresheet.get_round(game.round - 1)

            # create a holder for the shuffled cards
            holder = list()

            # deal
            for i in range(game.round - 1):
                holder.append(deck.pop(0))

            # arrange the cards TODO: how to sort by suit
            holder = sorted(holder)

            # reset the hand in the database
            round.hand = holder
            db.session.commit()

            # send hands to each player
            socketio.emit('deal_hand', {'hand': round.hand}, namespace=namespace, room=scoresheet.player)

        # set trump
        game.trump = deck.pop(0)
        socketio.emit('pass_trump', {'trump': game.trump}, namespace=namespace)
        db.session.commit()

        # if the trump is wizard, ask the dealer for a suit
        if game.trump[0] == "W":
            Game.choose_a_trump()
        #else get first bid
        else:
            Game.get_bid()


    @classmethod
    def choose_a_trump(cls):
        # get game and scoresheets
        game = cls.get_game()

        # get a list of players in position order, then select the dealer with game,round
        players = game.get_players()
        dealer = players[game.round]

        # request trump choice
        socketio.emit('choose_trump', namespace=namespace, room=dealer.player)

    @classmethod
    def receive_trump(cls, trump, chooser):
        # set trump to chosen suit
        game = cls.get_game()
        game.trump = trump
        db.session.commit()

        # tell everyone
        socketio.emit('server_message', {'message': chooser + ' chose ' + trump + ' for trump'}, namespace=namespace)

        # tell everyone to display trump
        socketio.emit('trump_chosen', trump, namespace=namespace)

        cls.get_bid()

    @classmethod
    def get_bid(cls):
        game = cls.get_game()
        players = game.get_players()
        bidder_index = game.get_bidder_index()
        bidder_name = players[bidder_index]

        #get total bid so far
        total_bid = game.get_total_bid()

        #let everyone know who's bidding
        socketio.emit('new_bidder', {'bidderIndex': bidder_index}, namespace=namespace)

        #tell the player it's their turn to bid
        send_data = {
            'roundNumber': game.round,
            'bidderIndex': bidder_index,
            'totalBid': total_bid
        }
        socketio.emit('your_bid', send_data, namespace=namespace, room=bidder_name)

    @classmethod
    def receive_bid(cls, passed_bid):
        game = cls.get_game()
        scoresheets = game.get_scoresheets()
        bidder_index = game.get_bidder_index()
        bidder_name = game.get_bidder_name()

        #save the bid and increase bid_index in the database
        bidder = scoresheets[bidder_index]
        round = bidder.rounds[i]
        round.bid = passed_bid
        game.bid_index += 1
        db.session.commit()

        # tell everyone what the person bid
        server_msg = bidder_name + " bid " + passed_bid
        bid_array = [scoresheet.rounds[game.round - 1].bid for scoresheet in scoresheets]
        socketio.emit('server_message', {'message': server_msg}, namespace=namespace)
        socketio.emit('refresh_bid', {'bidArray': bid_array}, namespace=namespace)

        # check if everyone has bid
        if bidder_index < number_of_players:
            socketio.emit('bidding_over', namespace=namespace)
            cls.get_bid()
        else:
            # let us know if we're under/overbid
            difference = game.get_total_bid() - game.round

            if difference > 0:
                message = "Total bid is " + game.get_total_bid() + ". We are " + abs(difference) + " underbid."
            else:
                message = "Total bid is " + game.get_total_bid() + ". We are " + abs(difference) + " overbid."

            socketio.emit('server_message', {'message': message}, namespace=namespace)

            cls.play_trick()

    @classmethod
    def play_trick(cls):
        game = cls.get_game()
        scoresheets = game.get_scoresheets()

        #add empty played cards container for this round to each scoresheet
        for scoresheet in scoresheets:
            scoresheet.played_cards.append([])

        #get the first players card
        cls.request_play_card()

    @classmethod
    def request_play_card(cls):
        game = cls.get_game()
        turn_name = game.get_turn_name()

        # tell next player it's their turn
        message = {'turn': game.round}
        socketio.emit('your_turn', message ,namespace=namespace, room=turn_name)

        # tell everyone who's turn it is
        message = turn_name + "\'s turn"
        socketio.emit('server_message', {'message': message}, namespace=namespace)


    @classmethod
    def receive_play_card(cls, card):
        game = cls.get_game()
        turn_index = game.get_turn_index()
        players = game.get_players()
        player = players[turn_index]

        # log who played what card
        msg = player + " played " + card
        socketio.emit('server_message', {'message': msg}, namespace=namespace)

        # add the played card to the database
        Scoresheet.played_cards[game.round].append(card)
        db.session.commit()

        # increase the turn counter
        game.turn_counter += 1
        db.session.commit()

        # if trick isn't over, get the next players card
        if game.turn_counter < number_of_players:
            cls.request_play_card()

        # if trick is over, score the trick
        else:
            cls.score_trick()

    @classmethod
    def score_trick(cls):
        game = cls.get_game()
        scoresheets = game.get_scoresheets()
        # list of cards played in order of position
        played_cards_by_position = game.get_played_cards(game.round, game.trick_counter)
        who_led = game.get_turn_index()
        played_cards_by_played_order = played_cards_by_position[who_led:] + played_cards_by_position[:who_led]
        trump = game.get_trump(game.round)

        #get led suit
        led_suit = played_cards_by_played_order[who_led][0]
        # TODO: is this correct
        led_suit = "X" if "W" == led_car or "J" == led_card else led_suit = led_suit[0]

        # helper function to check if a hand is all jacks
        def all_jesters(played_cards):
            for played_card in played_cards:
                if played_card[0] != "J":
                    return False
            return True

        # find the index of a wizard
        def find_wizard(played_cards):
            for i, card in enumerate(played_cards):
                if card[0] == 'W':
                    return i
            else:
                return -1

        # winner in this tree is the index of the winner where 0 = led card. we will need to add this to who_led to get the real index of the winner
        if all_jesters(played_cards_by_played_order):
            winner = 0
        elif find_wizard(played_cards_by_played_order) > -1:
            winner = find_wizard(played_cards_by_played_order)
        else:
            played_card_scores = []
            for i, card in enumerate(played_cards_by_played_order):
                if card[0] == trump:
                    played_card_scores.append(13 + card[1])
                elif card[0] == led_suit:
                    played_card_scores.append(card[1])
                else:
                    played_card_scores.append(0)
            winner = played_card_scores.index(max(played_card_scores))

        # calculate real index
        winner += who_led
        winner %= number_of_players

        # add a trick taken to the scoresheet and set the turn to the winner
        winner_scoresheet = scoresheets[winner]
        winner_scoresheet.rounds[game.round].tricks_taken += 1
        game.turn = winner
        game.trick_counter += 1
        db.session.commit()

        # let everyone know the winner
        message = {'message': winner_scoresheet.player + " won with " + played_cards_by_position[winner] +
                           ". Played cards: " + ", ".join(played_cards_by_played_order)}
        socketio.emit('server_message', message, namespace=namespace)

        # refresh trick_taken counters on client side
        tricks_taken = [scoresheet.get_tricks_taken_by_round(game.round) for scoresheet in scoresheets]
        socketio.emit('refresh_tricks_taken', {'tricksTaken': tricks_taken}, namespace=namespace)

        if game.trick_counter == game.round:
            Game.score_round()
        else:
            Game.play_trick()

    @classmethod
    def score_round(cls):
        game = cls.get_latest_counter()
        scores = cls.get_latest_counter().scores.order_by('position desc').all()
        scores.reverse()
        for score in scores:
            scoresheet = hand_to_list(score.score)
            stats = scoresheet[game.round - 1]
            tricks_taken = stats[0]
            bid = stats[1]
            if bid != tricks_taken:
                stats[2] = str(int(stats[2]) - abs(int(tricks_taken) - int(bid)) * 10)
            else:
                stats[2] = str(int(stats[2]) + 20 + (int(tricks_taken) - int(bid)) * 10)
            score.score = hand_to_string(scoresheet)
        db.session.commit()
        Game.send_game_data()
        Game.play_round()


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer)
    name = db.Column(db.String(64), index=True, unique=True, )
    results = db.relationship('Score', backref='players', lazy='dynamic')

    def __repr__(self):
        return str(self.name)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

    def get_player_info(self):
        return dict(name=self.name)


class Scoresheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player = db.Column(db.Integer, db.ForeignKey('player.name'))
    game = db.Column(db.Integer, db.ForeignKey('game.id'))
    ## TODO: rename score to rounds
    rounds = db.Column(db.String)
    position = db.Column(db.Integer)
    played_cards = db.Column(db.String, default="[]")

    def __repr__(self):
        return "<player %r, score %r>" % (self.player, self.game)

    # call this method to change the score (will be rounds) table
    # 2nd arg round_number is optional - if it isn't there, this
    # returns a list of *copies* of this scoresheet's round objects in order of round #
    # if round_number argument round_number is passed,
    # this will return rounds[round_number object *not copies* TODO:both should be same return type
    def get_round(self, round_number):
        if round_number is None:
            return self.rounds[:]
        else:
            return self.rounds[round_number - 1]

    # returns bid for a given round#
    def get_bid_by_round(self, round_number):
        return self.rounds[round_number - 1].bid

    # returns tricks_taken for a given round
    def get_tricks_taken_by_round(self, round_number):
        return self.rounds[round_number - 1].tricks_taken

        # def get_score(self):
        #     game = self.get_latest_counter()
        #     scores = self.get_latest_counter().scores.order_by('position desc').all()
        #     scores.reverse()
        #     return dict(id=self.id, player=self.player, game=self.game, score=hand_to_list(self.score), position=self.position)

        # ## to access: Game --> scoresheets -->  round
        # class Round:
        #
        #     def __init__(self):
        #
        #
        #     def get_rounds(self):
        #
        #         return
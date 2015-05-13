from app import db, socketio
from flask import json
import random
from random import shuffle

# ###  A WORD ABOUT NOMENCLATURE  ####
# game_info = a row in the game table with round, turn, trick_counter, game_started/ended, trump. .scores gets associated rows from the scores table
# scoresheet = row in score table, which includes player, game, rounds, position
# rounds = list of objects that are each a round - index 0 is rd one, index 2 is rd two, etc.
#   round = {tricks_taken, bid, round_score, hand}
#
# card = two item list [suit, number]
# hand = a list of cards [[H,12],[W,00],etc.]
#

namespace = "/test"
number_of_players = 2  # TODO: make these properties of Game
number_of_rounds = 4

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round = db.Column(db.Integer, default=0)
    turn = db.Column(db.Integer, default=0)  # index for who will play a card next
    bid_index = db.Column(db.Integer, default=0)
    trick_counter = db.Column(db.Integer, default=0)
    game_started = db.Column(db.Boolean, default=False)
    time_started = db.Column(db.DateTime)
    game_ended = db.Column(db.Boolean, default=False)
    trump = db.Column(db.String)
    scores = db.relationship('Scoresheet', backref='game_object', lazy='dynamic')

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
        return [scoresheet.player for scoresheet in self.get_scoresheets()]

    def get_dealer_index(self, round):
        return self.round % (len(self.get_players()) - 1)

    def get_dealer_name(self, round):
        players = self.get_players()
        return players[self.get_dealer_index(round)]

    # returns the index of the nth bidder for this round
    def get_bidder_index(self):
        return (self.round + self.bid_index) % number_of_players

    def get_bidder_name(self):
        scoresheets = self.get_scoresheets()
        bidder_index = self.get_bidder_index()
        bidder_name = scoresheets[bidder_index].player
        return bidder_name

    def get_turn_index(self):
        return (self.round + self.turn) % number_of_players

    def get_turn_name(self):
        scoresheets = self.get_scoresheets()
        turn_index = self.get_turn_index()
        turn_name = scoresheets[turn_index].player
        return turn_name

    def get_total_bid_by_round(self, round_number):
        scoresheets = self.get_scoresheets()
        stats = [scoresheet.get_stats(round_number) for scoresheet in scoresheets]
        return reduce(lambda x, y: x.bid + y.bid, stats)

    def get_all_stats_by_round(self, round):
        scoresheets = self.get_scoresheets()
        return [scoresheet.get_stats() for scoresheet in scoresheets]

    # return a list of the cards played in a given trick and round
    def get_played_cards(self, round, trick):
        scoresheets = self.get_scoresheets()
        return [scoresheet.played_cards[round][trick] for scoresheet in scoresheets]

    # return trump given round
    def get_trump(self, round):
        return self.trump[round]

    def get_score_report(self, round):
        stats = self.get_latest_stats(round)
        scores = [stat.score for stat in stats]
        players = self.get_players()
        sorted_scores = sorted(scores)
        #makes sorted scores - leader keeps total score, others have difference
        sorted_scores.reverse()
        for index, score in sorted_scores:
            if index != 0:
                score -= sorted_scores[0]
        sorted_players = [players[scores.index(score)] for score in sorted_scores]
        sorted_players.reverse()

        score_message = [(sorted_players[index] + ": " + str(score)) for index, score in enumerate(score_report_scores)]
        " ".join(score_message)

    @classmethod
    def create_game(cls):
        #create row in game table
        game = Game(game_started=True)
        db.session.add(game)
        db.session.commit()

        #randomly passing order that will be assigned when we create scoresheets
        positions = range(0, number_of_players)
        random.shuffle(positions)

        #create a scoresheet for each player TODO: this is currently making a game from all players in the db
        players = Player.query.all()
        player_names = []
        for player in players:
            p = Scoresheet(player=player.name, game_id=game.id, position=positions.pop())
            db.session.add(p)
            db.session.commit()
            player_names.append(player.name)

            for i in range(0,number_of_rounds):
                r = Round(scoresheet_id=p.id, round_number=i+1)
                db.session.add(r)
        db.session.commit()

        # assemble data to be sent
        send_data = {'logMessage': 'game started','players': player_names}
        socketio.emit('start_game', send_data, namespace=namespace)

        #play the first round
        game.play_round()


    def play_round(self):
        #check if the game is over
        if self.round == number_of_rounds:
            print "game over!"
            return

        # increase round counter - round is 1 indexed, 1 == rd1
        self.round += 1
        # set who's turn it is to index 1 (dealer is index 0, so it's left of the dealer)
        self.turn = self.round
        db.session.commit()

        # let everyone know the round started
        socketio.emit('server_message', {'message': 'Round' + str(self.round) + "...FIGHT!!!"}, namespace=namespace)
        socketio.emit('update_round', {'round': self.round}, namespace=namespace)

        # shuffle up n deal
        self.deal()


    def deal(self):
        scoresheets = self.get_scoresheets()

        # build the deck
        deck = []
        suits = ['C', 'D', 'H', 'S']
        for suit in suits:
            for i in range(1, 14):
                deck.append([suit, i])
        for i in range(3):
            deck.append(["W", 27])
            deck.append(["J", 0])

        #shuffle
        shuffle(deck)

        # deal the cards
        for scoresheet in scoresheets:
            # select the hand from scoresheet object
            stat = scoresheet.get_stats(self.round)

            # TODO: better way to do this than use holder?
            # create a holder for the shuffled cards
            holder = list()

            # deal
            for i in range(self.round):
                holder.append(deck.pop(0))

            # arrange the cards TODO: how to sort by suit
            holder = sorted(holder)

            # reset the hand in the database
            stat.hand = json.dumps(holder)
            db.session.commit()

            # send hands to each player
            socketio.emit('deal_hand', {'hand': stat.hand}, namespace=namespace, room=scoresheet.player)

        # set trump
        self.trump = json.dumps(deck.pop(0))
        socketio.emit('pass_trump', {'trump': self.trump}, namespace=namespace)
        db.session.commit()

        # if the trump is wizard, ask the dealer for a suit
        if self.trump[0] == "W":
            self.choose_a_trump()
        #else get first bid
        else:
            self.get_bid()

    def choose_a_trump(self):
        # get a list of players in position order, then select the dealer with game,round
        players = self.get_players()
        dealer = self.get_dealer_name(self.round)

        # request trump choice
        socketio.emit('choose_trump', namespace=namespace, room=dealer.player)

    def receive_trump(self, trump, chooser):
        # set trump to chosen suit
        game.trump = trump
        db.session.commit()

        # tell everyone
        socketio.emit('server_message', {'message': chooser + ' chose ' + trump + ' for trump'}, namespace=namespace)

        # tell everyone to display trump
        socketio.emit('trump_chosen', trump, namespace=namespace)

        self.get_bid()

    def get_bid(self):
        players = self.get_players()
        bidder_index = self.get_bidder_index()
        bidder_name = players[bidder_index]

        #get total bid so far
        total_bid = self.get_total_bid_by_round(self.round)

        #let everyone know who's bidding
        socketio.emit('new_bidder', {'bidderIndex': bidder_index}, namespace=namespace)

        #tell the player it's their turn to bid
        send_data = {
            'roundNumber': self.round,
            'bidderIndex': bidder_index,
            'totalBid': total_bid
        }

        socketio.emit('your_bid', send_data, namespace=namespace, room=bidder_name)

    def receive_bid(self, passed_bid):
        scoresheets = self.get_scoresheets()
        bidder_index = self.get_bidder_index()
        bidder_name = self.get_bidder_name()

        #save the bid and increase bid_index in the database
        bidder = scoresheets[bidder_index]
        this_round = bidder.rounds[self.rounds]
        this_round.bid = passed_bid
        self.bid_index += 1
        db.session.commit()

        # tell everyone what the person bid
        server_msg = bidder_name + " bid " + passed_bid
        bid_list = [scoresheet.get_stats(self.round).bid for scoresheet in scoresheets]
        socketio.emit('server_message', {'message': server_msg}, namespace=namespace)
        socketio.emit('refresh_bid', {'bidArray': bid_list}, namespace=namespace)

        # check if everyone has bid
        if bidder_index == number_of_players:
            self.get_bid()

        # if we are done bidding, let everyone know and start a trick
        else:
            # let us know if we're under/overbid
            difference = self.get_total_bid_by_round(self.round) - self.round
            if difference > 0:
                message = "Total bid is " + self.get_total_bid_by_round(self.round) + ". We are " + abs(difference) + " underbid."
            else:
                message = "Total bid is " + self.get_total_bid_by_round(self.round) + ". We are " + abs(difference) + " overbid."

            socketio.emit('server_message', {'message': message}, namespace=namespace)

            self.request_play_card()

    def request_play_card(self):
        turn_name = self.get_turn_name()

        # tell next player it's their turn
        message = {'turn': self.round}
        socketio.emit('your_turn', message ,namespace=namespace, room=turn_name)

        # tell everyone who's turn it is
        message = turn_name + "\'s turn"
        socketio.emit('server_message', {'message': message}, namespace=namespace)

    def receive_play_card(self, card):
        turn_index = self.get_turn_index()
        players = self.get_players()
        player = players[turn_index]

        # log who played what card
        msg = {'message': player + " played " + card}
        socketio.emit('server_message', msg, namespace=namespace)

        # increase the turn counter
        self.turn_counter += 1
        db.session.commit()

        # if trick isn't over, get the next players card
        if self.turn_counter < number_of_players:
            self.request_play_card()

        # if trick is over, score the trick
        else:
            self.score_trick()

    @classmethod
    def score_trick(self):
        scoresheets = self.get_scoresheets()
        played_cards_by_position = self.get_played_cards(self.round, self.trick_counter)
        who_led = self.get_turn_index()
        played_cards_by_played_order = played_cards_by_position[who_led:] + played_cards_by_position[:who_led]
        trump = self.get_trump(self.round)

        #get led suit
        led_suit = played_cards_by_played_order[who_led][0]
        if led_suit == "W"  or led_suit == "J":
            led_suit = "X"

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

        # calculate position index from played card index
        winner += who_led
        winner %= number_of_players

        # add a trick taken to the scoresheet and set the turn to the winner
        winner_scoresheet = scoresheets[winner]
        winner_scoresheet.stats[self.round].tricks_taken += 1
        self.turn = winner
        self.trick_counter += 1
        db.session.commit()

        # let everyone know the winner
        message = {'message': winner_scoresheet.player + " won with " + played_cards_by_position[winner] +
                           ". Played cards: " + ", ".join(played_cards_by_played_order)}
        socketio.emit('server_message', message, namespace=namespace)

        # refresh trick_taken counters on client side
        tricks_taken = [scoresheet.get_stats(self.round) for scoresheet in scoresheets]
        socketio.emit('refresh_tricks_taken', {'tricksTaken': tricks_taken}, namespace=namespace)

        #if we've played all the tricks, score the round, if not play the next trick
        if self.trick_counter == self.round:
            self.score_round()
        else:
            self.play_trick()

    def score_round(self):
        scoresheets = self.get_scoresheets()

        # score the round for each player
        for scoresheet in scoresheets:
            this_round = scoresheet.get_stats(self.round)
            bid = this_round.bid
            tricks_taken = this_round.tricks_taken

            # check if it's the first round
            if self.round == 1:
                previous_round = scoresheet.get_stats(self.round - 1)
                previous_score = previous_round.score
            else:
                previous_score = 0

            # tally up the score
            if bid == tricks_taken:
                this_round.score = previous_score + 20 + 10*bid
            else:
                this_round.score = previous_score-10*abs(bid - tricks_taken)
        db.session.commit()

        #send data to add row to scorecard
        this_rounds_stats = [scoresheet.get_stats(game.round) for scoresheet in scoresheets]
        send_data = {
            'gameRound': self.round,
            'tricksTaken': this_rounds_stats}
        socketio.emit('update_scorecard', send_data, namespace=namespace)

        #log the action
        score_report = self.get_score_report()

        send_data = {'message': score_report}
        socketio.emit('server_message', send_data, namespace=namespace)

        #increment round counter, check if the game is over
        self.round += 1
        db.session.commit()
        if self.round == number_of_rounds:
            self.game_ended = True
            print 'Game Over'
        else:
            self.play_round()

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer)
    name = db.Column(db.String(64), index=True, unique=True, )
    results = db.relationship('Scoresheet', backref='players', lazy='dynamic')

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

class Scoresheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player = db.Column(db.Integer, db.ForeignKey('player.name'))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    position = db.Column(db.Integer)
    stats = db.relationship('Round', backref='sheet', lazy='dynamic')

    def __repr__(self):
        return "<scoresheet for player %r, game %r>" % (self.player, self.game_id)

    #returns the stats for a scoresheet by round in order of position
    def get_stats(self, round_num):
        stats = db.session.query(Round).filter_by(scoresheet_id=self.id,round_number=round_num).first()
        return stats

    # points to stats by
    def get_round(self, round_num):
        return self.rounds[round_num - 1]


class Round(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scoresheet_id = db.Column(db.Integer, db.ForeignKey('scoresheet.id'))
    round_number = db.Column(db.Integer)
    tricks_taken = db.Column(db.Integer, default=0)
    bid = db.Column(db.Integer, default=0)
    hand = db.Column(db.String, default='[]')
    played_cards = db.Column(db.String, default='[]')

    def __repr__(self):
        return "<round %r>" % (self.round_number)



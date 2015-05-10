from app import db, socketio
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
    player_count = db.Column(db.Integer, default=0)
    game_started = db.Column(db.Boolean, default=False)
    time_started = db.Column(db.DateTime)
    game_ended = db.Column(db.Boolean, default=False)
    trump = db.Column(db.String)
    scores = db.relationship('Scoresheet', backref='games', lazy='dynamic')

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

    def get_total_bid(self):
        scoresheets = self.get_scoresheets()
        return reduce(lambda x, y: x.get_round(game.round).bid + y.get_round(game.round).bid, scoresheets)

    def get_latest_stats(self):
        scoresheets = self.get_scoresheets()
        return [scoresheet.round[-1] for scoresheet in scoresheets]

    # returns list of scores in order of position
    def get_scores(self, round):
        scoresheets = self.get_latest_stats()
        [scoresheet.rounds[round - 1] for scoresheet in scoresheets]

    # return a list of the cards played in a given trick and round
    def get_played_cards(self, round, trick):
        scoresheets = self.get_scoresheets()
        return [scoresheet.played_cards[round][trick] for scoresheet in scoresheets]

    # return trump given round
    def get_trump(self, round):
        return self.trump[round]

    def get_score_report(self):
        stats = self.get_latest_stats()
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

        #randonly assing order that will be assigned when we create scoresheets
        positions = range(0, number_of_players)
        random.shuffle(positions)

        #create a scoresheet for each player TODO: this is currently making a game from all players in the db
        players = Player.query.all()
        for player in players:
            p = Scoresheet(player=player.name, game=game.id, position=positions.pop())
            db.session.add(p)
        db.session.commit()

        # assemble data to be sent
        send_data = {'logMessage': 'game started'}
        socketio.emit('start_game', send_data, namespace=namespace)

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
            print scoresheet.get_round(game.round)
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
            round = scoresheet.get_round(game.round)

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
        this_round = bidder.rounds[game.rounds]
        this_round.bid = passed_bid
        game.bid_index += 1
        db.session.commit()

        # tell everyone what the person bid
        server_msg = bidder_name + " bid " + passed_bid
        bid_array = [scoresheet.get_round(game.round).bid for scoresheet in scoresheets]
        socketio.emit('server_message', {'message': server_msg}, namespace=namespace)
        socketio.emit('refresh_bid', {'bidArray': bid_array}, namespace=namespace)

        # check if everyone has bid
        if bidder_index < number_of_players:
            socketio.emit('bidding_over', namespace=namespace)
            cls.get_bid()

        # if we are done bidding, let everyone know and start a trick
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

        #get the first player's card
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
        played_cards_by_position = game.get_played_cards(game.round, game.trick_counter)
        who_led = game.get_turn_index()
        played_cards_by_played_order = played_cards_by_position[who_led:] + played_cards_by_position[:who_led]
        trump = game.get_trump(game.round)

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
        winner_scoresheet.rounds[game.round].tricks_taken += 1
        game.turn = winner
        game.trick_counter += 1
        db.session.commit()

        # let everyone know the winner
        message = {'message': winner_scoresheet.player + " won with " + played_cards_by_position[winner] +
                           ". Played cards: " + ", ".join(played_cards_by_played_order)}
        socketio.emit('server_message', message, namespace=namespace)

        # refresh trick_taken counters on client side
        tricks_taken = [scoresheet.get_round(game.round) for scoresheet in scoresheets]
        socketio.emit('refresh_tricks_taken', {'tricksTaken': tricks_taken}, namespace=namespace)

        #if we've played all the tricks, score the round, if not play the next trick
        if game.trick_counter == game.round:
            Game.score_round()
        else:
            Game.play_trick()

    @classmethod
    def score_round(cls):
        game = cls.get_game()
        scoresheets = game.get_scoresheets()

        # score the round for each player
        for scoresheet in scoresheets:
            this_round = scoresheet.get_round(game.round)
            bid = this_round.bid
            tricks_taken = this_round.tricks_taken

            # check if it's the first round
            if game.round == 1:
                previous_round = scoresheet.get_round(game.round - 1)
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
        this_rounds_stats = [scoresheet.get_round(game.round) for scoresheet in scoresheets]
        send_data = {
            'gameRound': game.round,
            'tricksTaken': this_rounds_stats}
        socketio.emit('update_scorecard', send_data, namespace=namespace)

        #log the action
        score_report = game.get_score_report()

        send_data = {'message': score_message}
        socketio.emit('server_message', send_data, namespace=namespace)

        #increment round counter, check if the game is over
        game.round += 1
        db.session.commit()
        if game.round == number_of_rounds:
            game.game_ended = True
            print 'Game Over'
        else:
            cls.play_round()


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

    def get_player_info(self):
        return dict(name=self.name)


class Scoresheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player = db.Column(db.Integer, db.ForeignKey('player.name'))
    game = db.Column(db.Integer, db.ForeignKey('game.id'))
    rounds = db.Column(db.String)
    position = db.Column(db.Integer)
    played_cards = db.Column(db.String, default="[]")

    def __repr__(self):
        return "<player %r, score %r>" % (self.player, self.game)

    # points to the current round
    def get_round(self, round_number):
        if round_number is None:
            return self.rounds[:]
        else:
            return self.rounds[round_number - 1]
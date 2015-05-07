from app import db, socketio
import json, random, views
from flask.ext.login import current_user
from random import shuffle
from sqlalchemy import desc
from flask import redirect, url_for, jsonify
from flask.ext.socketio import SocketIO, emit, send, join_room, leave_room, close_room, disconnect

namespace = "/test"
number_of_players = 2
number_of_rounds = 4
usertracker = []

#functions for translating hands and played cards
def hand_to_list(hand):
    #hand ="1,1,20,'JJJ WWW'.1,1,20,'JJJ WWW'
    hands = hand.split(".")
    for i, hand in enumerate(hands):
        hands[i] = hand.split(',')
    return hands


def hand_to_string(hand):
    for i, x in enumerate(hand):
        hand[i] = ",".join(x)
    return ".".join(hand)


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round = db.Column(db.Integer, default=0)
    turn = db.Column(db.Integer, default=0)
    trick_counter = db.Column(db.Integer, default=0)
    player_count = db.Column(db.Integer, default=0)
    game_started = db.Column(db.Boolean, default=False)
    time_started = db.Column(db.DateTime)
    game_ended = db.Column(db.Boolean, default=False)
    played_cards = db.Column(db.String, default="")
    trump = db.Column(db.String)
    scores = db.relationship('Score', backref='games', lazy='dynamic')

    def __repr__(self):
        return "game# %r" % str(self.id)

    def get_game_info(self):
        return dict(id=self.id, round=self.round, turn=self.turn, played_cards=self.played_cards, player_count=self.player_count, game_started=self.game_started,
                    time_started=self.time_started, game_ended=self.game_ended, trump=self.trump)

    @classmethod
    def get_latest_counter(cls):
        return Game.query.order_by('id desc').first()

    @classmethod
    def create_game(cls):
        game = Game(game_started=True)
        db.session.add(game)
        positions = range(0, number_of_players)
        random.shuffle(positions)
        raw_players = Player.query.all()
        for player in raw_players:
            p = Score(player=player.name, game=game.id, position=positions.pop(), score="0,0,0,." )
            db.session.add(p)
        db.session.commit()
        raw_scores = cls.get_latest_counter().scores.order_by('position desc').all()
        raw_scores.reverse()
        scores = [score.player for score in raw_scores]
        send_data = {'data': {'log': 'game started', 'scores': scores}}
        socketio.emit('start_game',
                      send_data,
                      namespace=namespace)
        game.play_round()


    @classmethod
    def play_round(cls):
        game = cls.get_latest_counter()
        if game.round == number_of_rounds:
            print "game over!"
            return
        game.round += 1
        game.turn = game.round
        db.session.commit()
        socketio.emit('server_message', {'data': 'Round' + str(game.round) + "...FIGHT!!!"}, namespace=namespace)
        Game.deal()
        Game.send_start_data()
        Game.get_bid(0)


    @classmethod
    def deal(cls):
        deck = ["C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09", "C10", "C11", "C12", "C13", "JJJ", "WWW", "D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08", "D09", "D10", "D11", "D12", "D13", "JJJ", "WWW", "H01", "H02", "H03", "H04", "H05", "H06", "H07", "H08", "H09", "H10", "H11", "H12", "H13", "JJJ", "WWW", "S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S10", "S11", "S12", "S13", "JJJ", "WWW"]
        shuffle(deck)
        game = cls.get_latest_counter()
        round = cls.get_latest_counter().round
        raw_scores = cls.get_latest_counter().scores.order_by('position desc').all()
        raw_scores.reverse()
        for x in raw_scores:
            temp_hand = hand_to_list(x.score)
            holder = list()
            for i in range(round):


                ######throwing a string does not have append method
                holder.append(deck.pop(0))
                print holder
                holder = sorted(holder)
                holder = " ".join(holder)
                temp_hand[i][3] = holder
            x.score = hand_to_string(temp_hand)
        game.trump = deck.pop(0)
        if game.trump == "WWW":
            Game.choose_a_trump()
        db.session.commit()

    @classmethod
    def choose_a_trump(cls):
        game = cls.get_latest_counter()
        scores = cls.get_latest_counter().scores.order_by('position desc').all()
        scores.reverse()
        dealer = scores[game.round]
        socketio.emit('choose_trump', namespace=namespace, room=dealer.player)

    @classmethod
    def get_bid(cls, bidder):
        game = cls.get_latest_counter()
        scores = cls.get_latest_counter().scores.order_by('position desc').all()
        scores.reverse()
        game.send_game_data()
        send_data = {
            'data': {
                'rdnumber': game.round,
                'turntobid': (game.round + bidder) % number_of_players,
                'bidder': bidder
            }
        }
        socketio.emit(
            'bidder',
            send_data,
            namespace=namespace)

        socketio.emit(
            'your_bid',
            send_data,
            namespace=namespace,
            room=scores[(game.turn + bidder) % number_of_players].player
        )

    @classmethod
    def receive_bid(cls, bidder, bid):
        game = cls.get_latest_counter()
        scores = cls.get_latest_counter().scores.order_by('position desc').all()
        scores.reverse()
        whobid = (bidder + game.round) % number_of_players
        socketio.emit(
            'server_message',
            {'data': scores[whobid].player + ' bid ' + bid},
            namespace=namespace)

        temp_hand = hand_to_list(scores[whobid].score)
        temp_hand[game.round - 1][1] = bid
        temp_hand = hand_to_string(temp_hand)
        scores[whobid].score = temp_hand
        db.session.commit()

        if bidder < number_of_players - 1:
            Game.get_bid(bidder + 1)
        else:
            socketio.emit('bidding_over', namespace=namespace)
            Game.play_trick()


    @classmethod
    def play_trick(cls):
        Game.send_game_data()
        game = cls.get_latest_counter()
        scores = cls.get_latest_counter().scores.order_by('position desc').all()
        scores.reverse()
        socketio.emit(
            'your_turn',
            {'data': game.turn},
            namespace=namespace,
            room=scores[game.turn].player)

    @classmethod
    def play_card(cls, card):
        game = cls.get_latest_counter()
        scores = cls.get_latest_counter().scores.order_by('position desc').all()
        scores.reverse()
        socketio.emit('server_message', {'data': str(scores[game.turn].player) + " played " + card}, namespace=namespace)
        game.turn += 1
        game.turn %= number_of_players
        game.played_cards = game.played_cards+card

        db.session.commit()
        #if the trick isn't over
        if len(hand_to_list(game.played_cards)[0]) != number_of_players:
            game.played_cards += ","
            db.session.commit()
            Game.play_trick()
        #if the trick is over
        else:
            game.played_cards += "."
            Game.send_game_data()
            db.session.commit()
            Game.score_trick()

    @classmethod
    def score_trick(cls):
        game = cls.get_latest_counter()
        scores = cls.get_latest_counter().scores.order_by('position desc').all()
        scores.reverse()
        played_cards = hand_to_list(game.played_cards)[-2]
        trump = game.trump[0]
        if played_cards[0][0] == "J":
            led_suit = "x"
        else:
            led_suit = played_cards[0][0]
        holder = []
        if 'WWW' in played_cards:
            winner = played_cards.index("WWW")
        elif all(x == "JJJ" for x in played_cards):
            winner = 0
        else:
            for card in played_cards:
                if card == "JJJ":
                    holder.append(0)
                if card[0] == trump:
                    holder.append(13 + int(card[1:3]))
                elif card[0] == led_suit:
                    holder.append(int(card[1:3]))
                else:
                    holder.append(0)
            winner = holder.index(max(holder))
        #selects the next winner and next dealer by adding starting position to winning position
        winning_player = scores[(game.turn + winner) % number_of_players]

        #selects the scoresheet and turns it into a list
        score_holder = hand_to_list(winning_player.score)

        score_holder[game.round - 1][0] = str(int(score_holder[game.round - 1][0]) + 1)
        winning_player.score = hand_to_string(score_holder)
        game.trick_counter += 1
        game.turn = (game.turn + winner) % number_of_players
        Game.send_game_data()
        db.session.commit()
        socketio.emit(
            'server_message',
            {'data': str(winning_player.player) + " won with " + played_cards[winner] + ". Played cards: " + ", ".join(played_cards)}, namespace=namespace)
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
                stats[2] = str(int(stats[2]) - abs(int(tricks_taken) - int(bid))*10)
            else:
                print score.player + ": " + str(20 + (int(tricks_taken) - int(bid)*10)) + " | " + str(int(stats[2]) + 20 + (int(tricks_taken) - int(bid))*10)
                stats[2] = str(int(stats[2]) + 20 + int(tricks_taken) - int(bid)*10)
            print score
            score.score = hand_to_string(scoresheet)
        db.session.commit()
        Game.play_round()







    @classmethod
    def send_start_data(cls):
        for player in usertracker:
            gameinfo = cls.get_latest_counter().get_game_info()
            raw_scores = cls.get_latest_counter().scores.order_by('position desc').all()
            scores = [score.get_score() for score in raw_scores]
            scores.reverse()
            for score in scores:
                if score['player'] != player:
                    holder = score['score']
                    for i, x in enumerate(holder):
                        try:
                            holder[i][3] = 'redacted'
                        except IndexError:
                            pass
                    score['score'] = holder
            send_data = {
                'data': {
                    'scores': scores,
                    'game': gameinfo,
                }
            }
            socketio.emit('start',
                          send_data,
                          namespace=namespace,
                          room=player)


    @classmethod
    def send_game_data(cls):
        for player in usertracker:
            gameinfo = cls.get_latest_counter().get_game_info()
            raw_scores = cls.get_latest_counter().scores.order_by('position desc').all()
            scores = [score.get_score() for score in raw_scores]
            scores.reverse()
            for score in scores:
                if score['player'] != player:
                    holder = score['score']
                    for i, x in enumerate(holder):
                        try:
                            holder[i][3] = 'redacted'
                        except IndexError:
                            pass
                    score['score'] = holder
            send_data = {'data': {'scores': scores,
                                  'game': gameinfo,
                        }
            }
            socketio.emit('refresh',
                          send_data,
                          namespace=namespace,
                          room=player)


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

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player = db.Column(db.Integer, db.ForeignKey('player.name'))
    game = db.Column(db.Integer, db.ForeignKey('game.id'))
    score = db.Column(db.String)
    position = db.Column(db.Integer)
    #score is in a string format with '.' separating the rounds: 'TricksTaken,Bid,Score,Hand.TricksTaken,Bid,Score,Hand'

    def __repr__(self):
        return "<player %r, score %r>" % (self.player, self.score)

    def get_score(self):
        return dict(id=self.id, player=self.player, game=self.game, score=hand_to_list(self.score), position=self.position)

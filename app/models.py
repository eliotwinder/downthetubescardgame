from app import db, socketio
import json
from flask import redirect, url_for, jsonify
from flask.ext.socketio import SocketIO, emit, send, join_room, leave_room, close_room, disconnect

namespace = "/test"

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    score = db.Column(db.Integer)
    bid = db.Column(db.Integer)
    tricks_taken = db.Column(db.Integer)
    hand = db.Column(db.String(256))

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

    def __repr__(self):
        return str(self.name)

    def get_player_info(self):
        return dict(score=self.score, bid=self.bid, tricks_taken=self.tricks_taken, hand=self.hand)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round = db.Column(db.Integer, default=1)
    player_count = db.Column(db.Integer, default=0)
    game_started = db.Column(db.Boolean, default=False)
    time_started = db.Column(db.DateTime)
    game_ended = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return self.id

    def get_game_info(self):
        return dict(id=self.id, round=self.round, player_count=self.player_count, game_started= self.game_started, time_started=self.time_started, game_ended=self.game_ended)

    @classmethod
    def get_latest_counter(cls):
        return cls.query.order_by(cls.id.desc()).first()

    @classmethod
    def increment_counter(cls):
        game = cls.get_latest_counter()
        game.player_count += 1
        db.session.commit()
        print "player count:" + str(game.player_count)


    @classmethod
    def decrement_counter(cls):
        game = cls.get_latest_counter()
        game.player_count = 0
        db.session.commit()
        game = cls.get_latest_counter()
        print game.player_count


    @classmethod
    def create_game(cls):
        game = cls.get_latest_counter()
        socketio.emit('start_game',
            {'data': 'game started with ' + str(game.player_count) + ' players'},
            namespace='/test')
        cls.send_game_data()

    @classmethod
    def send_game_data(cls):
        raw_players = Player.query.all()
        players = {player.name: player.get_player_info() for player in raw_players}
        game = cls.get_latest_counter().get_game_info()
        print players
        print json.dumps(players)
        send_data = {'data': {'players': players,
                                'game': game
                            }
                      }
        socketio.emit('refresh',
                      json.dumps(send_data),
                      namespace=namespace)





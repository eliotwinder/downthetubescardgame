from app import db, socketio
import json, random
from sqlalchemy import desc
from flask import redirect, url_for, jsonify
from flask.ext.socketio import SocketIO, emit, send, join_room, leave_room, close_room, disconnect

namespace = "/test"
number_of_players = 4
number_of_rounds = 60 / number_of_players

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round = db.Column(db.Integer, default=1)
    turn = db.Column(db.Integer, default=1)
    player_count = db.Column(db.Integer, default=0)
    game_started = db.Column(db.Boolean, default=False)
    time_started = db.Column(db.DateTime)
    game_ended = db.Column(db.Boolean, default=False)
    scores = db.relationship('Score', backref='games', lazy='dynamic')

    def __repr__(self):
        return str(self.id)

    def get_game_info(self):
        return dict(id=self.id, round=self.round, player_count=self.player_count, game_started=self.game_started,
                    time_started=self.time_started, game_ended=self.game_ended)

    @classmethod
    def get_latest_counter(cls):
       return Game.query.all().order_by('id').first()
        # return cls.query.order_by(cls['id']).first()


    # @classmethod
    # def decrement_counter(cls):
    #     game = cls.get_latest_counter()
    #     game.player_count = 0
    #     db.session.commit()
    #     game = cls.get_latest_counter()
    #     print game.player_count

    @classmethod
    def get_scores(cls):
        scores = Score.query.filter_by(id=1)
        result = {}
        # for score in scores:
        #     holder = score.get_score()
        #     result[holder["player"]] = holder
        return result

    @classmethod
    def create_game(cls):
        game = Game(game_started=True)
        game.game_started = True
        game.round = 1
        db.session.add(game)
        positions = range(0, number_of_players)
        random.shuffle(positions)
        raw_players = Player.query.all()
        for player in raw_players:
            p = Score(player=player, game=game, position=positions.pop() )
            db.session.add(p)
        # db.session.commit()

        players = {player.position: player.get_player_info() for player in raw_players}
        socketio.emit('start_game',
                      {'data': {'log': 'game started with ' + str(game.player_count) + ' players',
                                'players': players
                        }
                      },
                      namespace=namespace)
        Game.play_round(game.round)

    @classmethod
    def play_round(cls, round):
        if round == number_of_rounds:
            print "game over!"
            return
        round += 1
        turn = round + 1
        game = cls.get_latest_counter()
        game_info = game.get_game_info()
        scores = game.get_scores()
        send_data = {'data': {'game': game_info,
                              'scores': scores,
                              'numberOfPlayers': number_of_players,
                              'turn': turn
                             }
                     }
        #request name function initializes refresh data
        socketio.emit('request_name', send_data, namespace=namespace)

    @classmethod
    def send_game_data(cls, name):
        gameinfo = cls.get_latest_counter().get_game_info()
        game = cls.get_latest_counter()
        raw_players = game.scores.all()
        players = {player.name: player.get_player_info() for player in raw_players}
        for player in players:
            if player != name:
                del players[player]['hand']
        send_data = {'data': {'players': players,
                              'game': gameinfo,
                              'numberOfPlayers': number_of_players
                    }
        }
        socketio.emit('refresh',
                      send_data,
                      namespace=namespace)


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer)
    name = db.Column(db.String(64), index=True, unique=True)
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

    def send_game_info(self, name):
        raw_players = Player.query.all()
        players = {player.name: player.get_player_info() for player in raw_players}
        game = self.get_latest_counter().get_game_info()
        send_data = {'data': {'players': players,
                              'game': game,
                              'numberOfPlayers': number_of_players
                    }
        }
        socketio.emit('refresh',
                      json.dumps(send_data),
                      namespace=namespace)

    def get_player_info(self):
        return dict(name=self.name)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player = db.Column(db.Integer, db.ForeignKey('player.id'))
    game = db.Column(db.Integer, db.ForeignKey('game.id'))
    score = db.Column(db.String)
    position = db.Column(db.Integer)

    def __repr__(self):
        return "<player %r, game %r>" % (self.player, self.score)

    def get_score(self):
        return dict(id=self.id, player=self.player, game=self.game, score=self.score, position=self.position)
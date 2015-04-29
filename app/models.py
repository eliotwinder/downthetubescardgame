from app import db
from flask.ext.socketio import SocketIO, emit, send, join_room, leave_room, close_room, disconnect

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
        return '%r' % ([self.name, self.score, self.bid, self.tricks_taken, self.hand])

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_count = db.Column(db.Integer, default=0)
    game_started = db.Column(db.Boolean, default=False)
    time_started = db.Column(db.DateTime)
    game_ended = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '%r' % ([self.id, self.player_count, self.game_started, self.time_started, self.game_ended])

    @classmethod
    def get_latest_counter(cls):
        return cls.query.order_by(cls.id.desc()).first()

    @classmethod
    def increment_counter(cls):
        game = cls.get_latest_counter()
        game.player_count += 1
        db.session.commit()
        print "player count:" + str(game.player_count)
        if game.player_count == 2:
            cls.create_game()
            pass

    @classmethod
    def decrement_counter(cls):
        game = cls.get_latest_counter()
        game.player_count -= 1
        print "player count:" + str(game.player_count)
        db.session.commit()

    @classmethod
    def create_game(cls):
        players = Player.query.all()
        game = cls.get_latest_counter()
        emit('start_game',
            {'data': game.player_count},
             broadcast=True)


from app import db

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
        return ''%r'' % (self.name)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_count = db.Column(db.Integer, default=0)
    game_started = db.Column(db.Boolean, default=False)
    time_started = db.Column(db.DateTime)
    game_ended = db.Column(db.Boolean, default=False)

    @classmethod
    def get_latest_counter(cls):
        return cls.query.order_by(cls.id.desc()).first()

    @classmethod
    def increment_counter(cls):
        game = cls.get_latest_counter()
        game.player_count += 1
        db.session.commit()
        if game.player_count == 4:
            cls.create_game()
            pass

    @classmethod
    def decrement_counter(cls):
        game = cls.get_latest_counter()
        game.player_count -= 1
        db.session.commit()

    @classmethod
    def create_game(cls):
        players = Player.query.all()
        Player[1].score += 1
        db.session.commit()


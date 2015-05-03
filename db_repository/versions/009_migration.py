from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
game = Table('game', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('player_count', INTEGER),
    Column('game_started', BOOLEAN),
    Column('time_started', DATETIME),
    Column('game_ended', BOOLEAN),
    Column('round', INTEGER),
    Column('turn', INTEGER),
)

player = Table('player', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('name', VARCHAR(length=64)),
    Column('score', INTEGER),
    Column('bid', INTEGER),
    Column('tricks_taken', INTEGER),
    Column('hand', VARCHAR(length=256)),
    Column('position', INTEGER),
    Column('gameid', INTEGER),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['game'].drop()
    pre_meta.tables['player'].drop()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['game'].create()
    pre_meta.tables['player'].create()

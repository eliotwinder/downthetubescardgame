from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
round = Table('round', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('scoresheet', Integer),
    Column('round', Integer),
    Column('tricks_taken', Integer),
    Column('bid', Integer),
    Column('hand', String, default=ColumnDefault('[]')),
    Column('played_cards', String, default=ColumnDefault('[]')),
)

game = Table('game', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('round', INTEGER),
    Column('turn', INTEGER),
    Column('player_count', INTEGER),
    Column('game_started', BOOLEAN),
    Column('time_started', DATETIME),
    Column('game_ended', BOOLEAN),
    Column('trump', VARCHAR),
    Column('trick_counter', INTEGER),
    Column('bid_index', INTEGER),
)

scoresheet = Table('scoresheet', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('player', INTEGER),
    Column('game', INTEGER),
    Column('rounds', VARCHAR),
    Column('position', INTEGER),
    Column('played_cards', VARCHAR),
)

scoresheet = Table('scoresheet', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('player', Integer),
    Column('game_id', Integer),
    Column('position', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['round'].create()
    pre_meta.tables['game'].columns['player_count'].drop()
    pre_meta.tables['scoresheet'].columns['game'].drop()
    pre_meta.tables['scoresheet'].columns['played_cards'].drop()
    pre_meta.tables['scoresheet'].columns['rounds'].drop()
    post_meta.tables['scoresheet'].columns['game_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['round'].drop()
    pre_meta.tables['game'].columns['player_count'].create()
    pre_meta.tables['scoresheet'].columns['game'].create()
    pre_meta.tables['scoresheet'].columns['played_cards'].create()
    pre_meta.tables['scoresheet'].columns['rounds'].create()
    post_meta.tables['scoresheet'].columns['game_id'].drop()

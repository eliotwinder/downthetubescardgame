from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
game = Table('game', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('round', Integer, default=ColumnDefault(1)),
    Column('turn', Integer, default=ColumnDefault(1)),
    Column('player_count', Integer, default=ColumnDefault(0)),
    Column('game_started', Boolean, default=ColumnDefault(False)),
    Column('time_started', DateTime),
    Column('game_ended', Boolean, default=ColumnDefault(False)),
)

player = Table('player', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('position', Integer),
    Column('name', String(length=64)),
)

score = Table('score', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('player', Integer),
    Column('game', Integer),
    Column('score', String),
    Column('position', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['game'].create()
    post_meta.tables['player'].create()
    post_meta.tables['score'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['game'].drop()
    post_meta.tables['player'].drop()
    post_meta.tables['score'].drop()

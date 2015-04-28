from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
counter = Table('counter', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('counter', INTEGER),
    Column('game_started', BOOLEAN),
    Column('time_started', DATETIME),
)

game = Table('game', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('player_count', Integer, default=ColumnDefault(0)),
    Column('game_started', Boolean, default=ColumnDefault(False)),
    Column('time_started', DateTime),
    Column('game_ended', Boolean, default=ColumnDefault(False)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['counter'].drop()
    post_meta.tables['game'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['counter'].create()
    post_meta.tables['game'].drop()

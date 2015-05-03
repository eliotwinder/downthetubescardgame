from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
player = Table('player', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('gameid', Integer),
    Column('position', Integer),
    Column('name', String(length=64)),
    Column('score', Integer),
    Column('bid', Integer),
    Column('tricks_taken', Integer),
    Column('hand', String(length=256)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['player'].columns['gameid'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['player'].columns['gameid'].drop()

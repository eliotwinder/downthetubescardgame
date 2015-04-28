from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
counter = Table('counter', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('counter', Integer, default=ColumnDefault(0)),
    Column('game_started', Boolean, default=ColumnDefault(False)),
    Column('time_started', DateTime),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['counter'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['counter'].drop()

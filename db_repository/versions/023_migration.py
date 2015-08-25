from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
migration_tmp = Table('migration_tmp', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('position', INTEGER),
    Column('name', VARCHAR(length=64)),
    Column('bot', BOOLEAN),
)

player = Table('player', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('position', Integer),
    Column('name', String(length=64)),
)

scoresheet = Table('scoresheet', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('player', Integer),
    Column('game_id', Integer),
    Column('position', Integer),
    Column('bot', Boolean),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['migration_tmp'].drop()
    post_meta.tables['player'].create()
    post_meta.tables['scoresheet'].columns['bot'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['migration_tmp'].create()
    post_meta.tables['player'].drop()
    post_meta.tables['scoresheet'].columns['bot'].drop()

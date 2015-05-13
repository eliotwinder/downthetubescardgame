from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
round = Table('round', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('scoresheet', INTEGER),
    Column('round', INTEGER),
    Column('tricks_taken', INTEGER),
    Column('bid', INTEGER),
    Column('hand', VARCHAR),
    Column('played_cards', VARCHAR),
)

round = Table('round', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('scoresheet_id', Integer),
    Column('round_number', Integer),
    Column('tricks_taken', Integer, default=ColumnDefault(0)),
    Column('bid', Integer, default=ColumnDefault(0)),
    Column('hand', String, default=ColumnDefault([])),
    Column('played_cards', String, default=ColumnDefault([])),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['round'].columns['round'].drop()
    pre_meta.tables['round'].columns['scoresheet'].drop()
    post_meta.tables['round'].columns['round_number'].create()
    post_meta.tables['round'].columns['scoresheet_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['round'].columns['round'].create()
    pre_meta.tables['round'].columns['scoresheet'].create()
    post_meta.tables['round'].columns['round_number'].drop()
    post_meta.tables['round'].columns['scoresheet_id'].drop()

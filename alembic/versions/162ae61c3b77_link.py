"""link

Revision ID: 162ae61c3b77
Revises: ed5d6691ad56
Create Date: 2023-11-14 02:48:08.100559

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = '162ae61c3b77'
down_revision: Union[str, None] = 'ed5d6691ad56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('building_metro_link',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('building_id', sa.Integer(), nullable=True),
    sa.Column('metro_station_id', sa.Integer(), nullable=True),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['building_id'], ['building.id'], ),
    sa.ForeignKeyConstraint(['metro_station_id'], ['metro_station.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_constraint('building_group_metro_id_fkey', 'building_group', type_='foreignkey')
    op.drop_column('building_group', 'metro_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('building_group', sa.Column('metro_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('building_group_metro_id_fkey', 'building_group', 'metro_station', ['metro_id'], ['id'])
    op.drop_table('building_metro_link')
    # ### end Alembic commands ###

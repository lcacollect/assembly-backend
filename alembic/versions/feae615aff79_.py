"""empty message

Revision ID: feae615aff79
Revises: e76a2af25d73
Create Date: 2023-09-18 15:45:46.959901

"""
import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision = "feae615aff79"
down_revision = "e76a2af25d73"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("assemblyepdlink", sa.Column("transport_type", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column("assemblyepdlink", sa.Column("transport_distance", sa.Float(), nullable=True))
    op.add_column("assemblyepdlink", sa.Column("transport_unit", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("assemblyepdlink", "transport_unit")
    op.drop_column("assemblyepdlink", "transport_distance")
    op.drop_column("assemblyepdlink", "transport_type")
    # ### end Alembic commands ###
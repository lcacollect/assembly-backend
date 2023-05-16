"""empty message

Revision ID: a68b8abea315
Revises: e9fd94a0cdca
Create Date: 2022-08-10 10:46:37.177025

"""
import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision = "a68b8abea315"
down_revision = "e9fd94a0cdca"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("epd", sa.Column("origin_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.create_unique_constraint("origin_version", "epd", ["origin_id", "version"])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    op.drop_constraint("origin_version", "epd", type_="unique")
    op.drop_column("epd", "origin_id")
    # ### end Alembic commands ###

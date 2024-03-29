"""empty message

Revision ID: 34bef80465c3
Revises: 6f26c2bc974f
Create Date: 2023-05-19 11:08:53.615061

"""
import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision = "34bef80465c3"
down_revision = "6f26c2bc974f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint("assembly_id_unique", "assembly", ["id"])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("assembly_id_unique", "assembly", type_="unique")
    # ### end Alembic commands ###

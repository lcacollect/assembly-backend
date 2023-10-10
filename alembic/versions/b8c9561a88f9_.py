"""empty message

Revision ID: b8c9561a88f9
Revises: 1c9cfc006c7e
Create Date: 2023-10-09 10:27:45.473623

"""
import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b8c9561a88f9"
down_revision = "1c9cfc006c7e"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("assemblyepdlink", sa.Column("transport_conversion_factor", sa.Float(), nullable=False))
    op.add_column("assemblyepdlink", sa.Column("transport_epd_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.alter_column(
        "assemblyepdlink", "transport_distance", existing_type=postgresql.DOUBLE_PRECISION(precision=53), nullable=False
    )
    op.create_foreign_key("assemblyepdlink_epd_fkey", "assemblyepdlink", "epd", ["transport_epd_id"], ["id"])
    op.drop_column("assemblyepdlink", "transport_type")
    op.drop_column("assemblyepdlink", "transport_unit")
    op.add_column("projectassemblyepdlink", sa.Column("transport_conversion_factor", sa.Float(), nullable=False))
    op.alter_column(
        "projectassemblyepdlink",
        "transport_distance",
        existing_type=postgresql.DOUBLE_PRECISION(precision=53),
        nullable=False,
    )
    op.drop_column("projectassemblyepdlink", "transport_type")
    op.drop_column("projectassemblyepdlink", "transport_unit")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "projectassemblyepdlink", sa.Column("transport_unit", sa.VARCHAR(), autoincrement=False, nullable=True)
    )
    op.add_column(
        "projectassemblyepdlink", sa.Column("transport_type", sa.VARCHAR(), autoincrement=False, nullable=True)
    )
    op.alter_column(
        "projectassemblyepdlink",
        "transport_distance",
        existing_type=postgresql.DOUBLE_PRECISION(precision=53),
        nullable=True,
    )
    op.drop_column("projectassemblyepdlink", "transport_conversion_factor")
    op.add_column("assemblyepdlink", sa.Column("transport_unit", sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column("assemblyepdlink", sa.Column("transport_type", sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint("assemblyepdlink_epd_fkey", "assemblyepdlink", type_="foreignkey")
    op.alter_column(
        "assemblyepdlink", "transport_distance", existing_type=postgresql.DOUBLE_PRECISION(precision=53), nullable=True
    )
    op.drop_column("assemblyepdlink", "transport_epd_id")
    op.drop_column("assemblyepdlink", "transport_conversion_factor")
    # ### end Alembic commands ###

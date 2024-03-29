"""empty message

Revision ID: 7523b7b167ae
Revises: feae615aff79
Create Date: 2023-09-22 12:52:32.793106

"""
import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "7523b7b167ae"
down_revision = "feae615aff79"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.rename_table("assembly", "projectassembly")
    op.execute("ALTER INDEX assembly_pkey RENAME TO projectassembly_pkey")
    op.execute("ALTER INDEX assembly_id_unique RENAME TO projectassembly_id_unique")
    op.execute("ALTER INDEX ix_assembly_name RENAME TO ix_projectassembly_name")
    op.alter_column("projectassembly", "project_id", existing_type=sa.VARCHAR(), nullable=False)

    op.rename_table("assemblyepdlink", "projectassemblyepdlink")
    op.execute("ALTER INDEX assemblyepdlink_pkey RENAME TO projectassemblyepdlink_pkey")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("projectassembly", "project_id", existing_type=sa.VARCHAR(), nullable=True)
    op.rename_table("projectassembly", "assembly")
    op.execute("ALTER INDEX projectassembly_pkey RENAME TO assembly_pkey")
    op.execute("ALTER INDEX projectassembly_id_unique RENAME TO assembly_id_unique")
    op.execute("ALTER INDEX ix_projectassembly_name RENAME TO ix_assembly_name")

    op.rename_table("projectassemblyepdlink", "assemblyepdlink")
    op.execute("ALTER INDEX projectassemblyepdlink_pkey RENAME TO assemblyepdlink_pkey")

    # ### end Alembic commands ###

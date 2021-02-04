"""Add age gate to ads messages

Revision ID: 0dde5c5c7e07
Revises: b24a6ed2c08b
Create Date: 2021-02-02 08:30:40.244561

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0dde5c5c7e07'
down_revision = 'b24a6ed2c08b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('ads_messages', sa.Column('age_gate', sa.String(50), nullable=True))


def downgrade():
    op.drop_column('ads_messages', 'age_gate')

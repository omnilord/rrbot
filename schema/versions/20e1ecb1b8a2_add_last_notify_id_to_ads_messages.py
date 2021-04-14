"""add last notify id to ads messages

Revision ID: 20e1ecb1b8a2
Revises: 0dde5c5c7e07
Create Date: 2021-04-11 14:39:35.333539

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20e1ecb1b8a2'
down_revision = '0dde5c5c7e07'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('ads_messages', sa.Column('last_notice_id', sa.BigInteger, nullable=True, index=True))


def downgrade():
    op.drop_column('ads_messages', 'last_notice_id')

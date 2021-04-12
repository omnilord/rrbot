"""Create ads moderation schemas

Revision ID: b24a6ed2c08b
Revises: a2bc71b837b9
Create Date: 2021-01-07 02:52:36.499155

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b24a6ed2c08b'
down_revision = 'a2bc71b837b9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ads_channels',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=False),
        sa.Column('server_id', sa.BigInteger, nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('invites', sa.Boolean, nullable=False, server_default='1'),
        sa.Column('webhook_url', sa.String(255), nullable=True), # None = inactive
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('jsondata', sa.JSON)
    )
    op.create_table(
        'ads_messages',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=False),
        sa.Column('channel_id', sa.BigInteger, nullable=False, index=True),
        sa.Column('server_id', sa.BigInteger, nullable=False, index=True),
        sa.Column('author_id', sa.BigInteger, nullable=False, index=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=True),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('deleted_by_id', sa.BigInteger, nullable=True),
        sa.Column('invite_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('invite_code', sa.String(20), nullable=True),
        sa.Column('invite_server_id', sa.BigInteger, nullable=True, index=True),
        sa.Column('invite_server_name', sa.String(100), nullable=True),
        sa.Column('invite_expires_at', sa.DateTime, nullable=True)
    )
    op.create_table(
        'ads_warnings',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('ads_message_id', sa.BigInteger, nullable=False, index=True),
        sa.Column('author_id', sa.BigInteger, nullable=False, index=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by_id', sa.BigInteger, nullable=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('deleted_by_id', sa.BigInteger, nullable=True, index=True),
        sa.Column('jsondata', sa.JSON) # { "notes": [ { "user_id": #, "created_at": "", "note": "" } ] }
    )
    op.add_column(
        'servers',
        sa.Column('timezone', sa.String(32), nullable=True, server_default='America/New_York')
    )


def downgrade():
    op.drop_column('servers', 'timezone')
    op.drop_table('ads_warnings')
    op.drop_table('ads_messages')
    op.drop_table('ads_channels')

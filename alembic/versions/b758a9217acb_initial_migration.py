"""Initial migration

Revision ID: b758a9217acb
Revises: 
Create Date: 2026-05-04 20:33:18.123456

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg


# revision identifiers, used by Alembic.
revision = 'b758a9217acb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated ###
    op.create_table(
        'metadata',
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('last_sync_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_changed_at', sa.String(), server_default='2000-01-01', nullable=False),
        sa.Column('sync_status', sa.String(), server_default='unsynced', nullable=False),
        sa.PrimaryKeyConstraint('key'),
        sa.Index('ix_metadata_key', 'key'),
    )

    op.create_table(
        'places',
        sa.Column('id', pg.UUID(), nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('city', sa.String(), nullable=False),
        sa.Column('address', sa.String(), nullable=False),
        sa.Column('seats_pattern', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_places_id', 'id'),
    )

    op.create_table(
        'events',
        sa.Column('id', pg.UUID(), nullable=False),
        sa.Column('place_id', pg.UUID(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('event_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('registration_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('number_of_visitors', sa.Integer(), nullable=True),
        sa.Column('status_changed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['place_id'], ['places.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_events_id', 'id'),
        sa.Index('ix_events_place_id', 'place_id'),
    )

    op.create_table(
        'tickets',
        sa.Column('id', pg.UUID(), nullable=False),
        sa.Column('event_id', pg.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_tickets_id', 'id'),
        sa.Index('ix_tickets_event_id', 'event_id'),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated ###
    op.drop_table('tickets')
    op.drop_table('events')
    op.drop_table('places')
    op.drop_table('metadata')
    # ### end Alembic commands ###
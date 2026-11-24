"""brand preset field

Revision ID: 3f4bb8eaba14
Revises: e610c0e43cc3
Create Date: 2026-11-24 21:29:40.642174

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f4bb8eaba14'
down_revision: Union[str, Sequence[str], None] = 'e610c0e43cc3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


brands = sa.table("brands", sa.column("id", sa.Integer), sa.column("config", sa.JSON))


def _update(change) -> None:
    conn = op.get_bind()
    for row in conn.execute(sa.select(brands.c.id, brands.c.config)).all():
        config = dict(row.config)
        change(config)
        conn.execute(brands.update().where(brands.c.id == row.id).values(config=config))


def upgrade() -> None:
    """Data: every brand gets `preset` (story when it uses story mode); the old per-brand prompt folders
    are now the preset prompts, so `prompts` (own overrides) becomes empty."""
    def change(config):
        config["preset"] = "story" if config.get("script_mode") == "story" else "facts"
        config["prompts"] = None
    _update(change)


def downgrade() -> None:
    def change(config):
        config["prompts"] = "absurd_stories" if config.pop("preset", "facts") == "story" else "mind_facts"
    _update(change)

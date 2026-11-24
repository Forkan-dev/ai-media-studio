"""voice cfg_weight backfill

Revision ID: a102b24e360d
Revises: bac03fe5afb9
Create Date: 2026-11-25 00:54:49.159382

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a102b24e360d'
down_revision: Union[str, Sequence[str], None] = 'bac03fe5afb9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


brands = sa.table("brands", sa.column("id", sa.Integer), sa.column("config", sa.JSON))


def _update(change) -> None:
    conn = op.get_bind()
    for row in conn.execute(sa.select(brands.c.id, brands.c.config)).all():
        config = dict(row.config)
        config["voice"] = change(dict(config.get("voice", {})))
        conn.execute(brands.update().where(brands.c.id == row.id).values(config=config))


def upgrade() -> None:
    """Data: every brand gets the new voice.cfg_weight (pace) with its default, so all brands keep the same
    parameters."""
    _update(lambda v: {**v, "cfg_weight": v.get("cfg_weight", 0.5)})


def downgrade() -> None:
    _update(lambda v: {k: x for k, x in v.items() if k != "cfg_weight"})

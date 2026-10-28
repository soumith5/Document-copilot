"""add profile auto-creation trigger

Revision ID: b852e78ec93d
Revises: 7a6bad1291d8
Create Date: 2026-07-13 23:22:16.785315

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b852e78ec93d'
down_revision: Union[str, Sequence[str], None] = '7a6bad1291d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    # Function: copies id + email from a newly created auth.users row
    # into public.profiles. ON CONFLICT guards against re-running this
    # for a user that (somehow) already has a profile.
    op.execute(
        """
        create or replace function public.handle_new_user()
        returns trigger
        language plpgsql
        security definer set search_path = public
        as $$
        begin
          insert into public.profiles (id, email)
          values (new.id, new.email)
          on conflict (id) do nothing;
          return new;
        end;
        $$;
        """
    )

    # Trigger: fires after every signup in Supabase's auth.users table.
    op.execute(
        """
        drop trigger if exists on_auth_user_created on auth.users;
        create trigger on_auth_user_created
          after insert on auth.users
          for each row execute procedure public.handle_new_user();
        """
    )

    # One-time backfill: create profiles for any auth.users created
    # before this trigger existed (e.g. test accounts from Phase 3).
    op.execute(
        """
        insert into public.profiles (id, email)
        select id, email from auth.users
        on conflict (id) do nothing;
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("drop trigger if exists on_auth_user_created on auth.users;")
    op.execute("drop function if exists public.handle_new_user();")
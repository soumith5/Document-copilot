"""fix profile auto-creation trigger to guard on email, not id

Revision ID: a1f9c3d7e5b2
Revises: b852e78ec93d
Create Date: 2026-07-27

The original trigger (b852e78ec93d) used `on conflict (id)`, but id is
always a fresh UUID per signup — that clause can never actually fire.
The real constraint that fails is profiles_email_key (unique on email),
which happens whenever someone attempts to sign up again with an email
that already has a profile (e.g. a duplicate/retry signup). Since the
insert wasn't guarded against that specific conflict, it failed outright,
rolling back the entire auth.users insert transaction and surfacing as a
generic 500 on /auth/v1/signup.
"""
from alembic import op


revision = "a1f9c3d7e5b2"
down_revision = "f3a1c9d24e7b"
branch_labels = None
depends_on = None


def upgrade() -> None:
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
          on conflict (email) do nothing;
          return new;
        end;
        $$;
        """
    )


def downgrade() -> None:
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
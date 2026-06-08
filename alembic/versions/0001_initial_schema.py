"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-08
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roles")),
    )
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)

    op.create_table(
        "business_elements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_business_elements")),
    )
    op.create_index(op.f("ix_business_elements_name"), "business_elements", ["name"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("middle_name", sa.String(length=100), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], name=op.f("fk_users_role_id_roles")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_is_active"), "users", ["is_active"], unique=False)

    op.create_table(
        "access_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("element_id", sa.Integer(), nullable=False),
        sa.Column("read_permission", sa.Boolean(), nullable=False),
        sa.Column("read_all_permission", sa.Boolean(), nullable=False),
        sa.Column("create_permission", sa.Boolean(), nullable=False),
        sa.Column("update_permission", sa.Boolean(), nullable=False),
        sa.Column("update_all_permission", sa.Boolean(), nullable=False),
        sa.Column("delete_permission", sa.Boolean(), nullable=False),
        sa.Column("delete_all_permission", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["element_id"], ["business_elements.id"], name=op.f("fk_access_rules_element_id_business_elements")),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], name=op.f("fk_access_rules_role_id_roles")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_access_rules")),
        sa.UniqueConstraint("role_id", "element_id", name="uq_access_rules_role_element"),
    )

    for table_name, extra_columns in {
        "products": [
            sa.Column("price", sa.Numeric(10, 2), nullable=False),
            sa.Column("stock", sa.Integer(), nullable=False),
        ],
        "orders": [
            sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
            sa.Column("status", sa.String(length=40), nullable=False),
        ],
        "stores": [
            sa.Column("address", sa.String(length=255), nullable=True),
        ],
    }.items():
        op.create_table(
            table_name,
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("owner_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            *extra_columns,
            sa.ForeignKeyConstraint(["owner_id"], ["users.id"], name=op.f(f"fk_{table_name}_owner_id_users")),
            sa.PrimaryKeyConstraint("id", name=op.f(f"pk_{table_name}")),
        )
        op.create_index(op.f(f"ix_{table_name}_owner_id"), table_name, ["owner_id"], unique=False)

    op.create_table(
        "token_blacklist",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_token_blacklist_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_token_blacklist")),
    )
    op.create_index(op.f("ix_token_blacklist_expires_at"), "token_blacklist", ["expires_at"], unique=False)
    op.create_index(op.f("ix_token_blacklist_jti"), "token_blacklist", ["jti"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_token_blacklist_jti"), table_name="token_blacklist")
    op.drop_index(op.f("ix_token_blacklist_expires_at"), table_name="token_blacklist")
    op.drop_table("token_blacklist")
    for table_name in ("stores", "orders", "products"):
        op.drop_index(op.f(f"ix_{table_name}_owner_id"), table_name=table_name)
        op.drop_table(table_name)
    op.drop_table("access_rules")
    op.drop_index(op.f("ix_users_is_active"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_business_elements_name"), table_name="business_elements")
    op.drop_table("business_elements")
    op.drop_index(op.f("ix_roles_name"), table_name="roles")
    op.drop_table("roles")
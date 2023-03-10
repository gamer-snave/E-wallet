"""empty message

Revision ID: 0a5610e5dbe8
Revises: 219755035d55
Create Date: 2023-03-10 12:49:35.120501

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0a5610e5dbe8'
down_revision = '219755035d55'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('withdraw',
    sa.Column('withdraw_id', sa.Integer(), nullable=False),
    sa.Column('transaction_id', sa.String(length=50), nullable=False),
    sa.Column('account_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('completed', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['account_id'], ['account.account_id'], name=op.f('fk_withdraw_account_id_account')),
    sa.PrimaryKeyConstraint('withdraw_id', name=op.f('pk_withdraw')),
    sa.UniqueConstraint('transaction_id', name=op.f('uq_withdraw_transaction_id'))
    )
    with op.batch_alter_table('payment', schema=None) as batch_op:
        batch_op.alter_column('transaction_date',
               existing_type=sa.DATETIME(),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('payment', schema=None) as batch_op:
        batch_op.alter_column('transaction_date',
               existing_type=sa.DATETIME(),
               nullable=False)

    op.drop_table('withdraw')
    # ### end Alembic commands ###

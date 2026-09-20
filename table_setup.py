from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    CheckConstraint,
    Index,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


DATABASE_URL = "sqlite:///D:\\TradingData\\trading.db"

# ============================================================
# Base
# ============================================================

class Base(DeclarativeBase):
    pass


# ============================================================
# Account
# ============================================================

class Account(Base):
    __tablename__ = "accounts"

    account_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    account_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    broker: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    broker_account_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="USD",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )

    # Relationships
    trades: Mapped[list["Trade"]] = relationship(
        back_populates="account",
    )

    positions: Mapped[list["Position"]] = relationship(
        back_populates="account",
    )

    def __repr__(self):
        return (
            f"<Account("
            f"id={self.account_id}, "
            f"name={self.account_name}, "
            f"broker={self.broker}"
            f")>"
        )


# ============================================================
# Trade
# ============================================================

class Trade(Base):
    """
    Immutable execution record.

    A trade represents an actual execution, not a position.

    biz_date:
        Trading/business date associated with the execution.

    executed_at:
        Actual execution timestamp.

    created_at:
        Timestamp when the trade entered our database.
    """

    __tablename__ = "trades"

    trade_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.account_id"),
        nullable=False,
    )

    biz_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    instrument_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    side: Mapped[str] = mapped_column(
        String(4),
        nullable=False,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
    )

    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    commission: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        default=Decimal("0"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )

    # Relationships
    account: Mapped["Account"] = relationship(
        back_populates="trades",
    )

    __table_args__ = (
        CheckConstraint(
            "side IN ('BUY', 'SELL')",
            name="ck_trade_side",
        ),
        CheckConstraint(
            "quantity > 0",
            name="ck_trade_quantity_positive",
        ),
        CheckConstraint(
            "price >= 0",
            name="ck_trade_price_nonnegative",
        ),
        Index(
            "ix_trades_account_biz_date",
            "account_id",
            "biz_date",
        ),
        Index(
            "ix_trades_account_instrument",
            "account_id",
            "instrument_id",
        ),
    )

    def __repr__(self):
        return (
            f"<Trade("
            f"id={self.trade_id}, "
            f"account={self.account_id}, "
            f"instrument={self.instrument_id}, "
            f"side={self.side}, "
            f"qty={self.quantity}, "
            f"price={self.price}"
            f")>"
        )


# ============================================================
# Position
# ============================================================

class Position(Base):
    """
    Bi-temporal position record.

    VALID TIME
    ----------
    valid_from / valid_to

    Represents the period during which this position state
    is considered economically valid.

    SYSTEM TIME
    -----------
    update_time_from / update_time_to

    Represents when this version existed in our database.

    A correction therefore creates a new Position row rather
    than overwriting historical information.
    """

    __tablename__ = "positions"

    position_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.account_id"),
        nullable=False,
    )

    instrument_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # --------------------------------------------------------
    # Position state
    # --------------------------------------------------------

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    average_price: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
    )

    # --------------------------------------------------------
    # Business / valid time
    # --------------------------------------------------------

    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    valid_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # --------------------------------------------------------
    # System / update time
    # --------------------------------------------------------

    update_time_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )

    update_time_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # --------------------------------------------------------
    # Relationships
    # --------------------------------------------------------

    account: Mapped["Account"] = relationship(
        back_populates="positions",
    )

    __table_args__ = (
        CheckConstraint(
            "valid_to IS NULL OR valid_to > valid_from",
            name="ck_position_valid_interval",
        ),
        CheckConstraint(
            "update_time_to IS NULL "
            "OR update_time_to > update_time_from",
            name="ck_position_update_interval",
        ),
        Index(
            "ix_positions_account_instrument",
            "account_id",
            "instrument_id",
        ),
        Index(
            "ix_positions_valid_time",
            "account_id",
            "instrument_id",
            "valid_from",
            "valid_to",
        ),
        Index(
            "ix_positions_system_time",
            "account_id",
            "instrument_id",
            "update_time_from",
            "update_time_to",
        ),
    )

    def __repr__(self):
        return (
            f"<Position("
            f"id={self.position_id}, "
            f"account={self.account_id}, "
            f"instrument={self.instrument_id}, "
            f"qty={self.quantity}, "
            f"valid={self.valid_from}->{self.valid_to}, "
            f"system={self.update_time_from}->{self.update_time_to}"
            f")>"
        )

class Instrument(Base):
    __tablename__ = "instruments"

    instrument_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    symbol: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    underlying: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    instrument_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    exchange: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="USD",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )

    trades: Mapped[list["Trade"]] = relationship(
        "Trade",
        back_populates="instrument",
    )

def create_database():
    engine = create_engine(
        DATABASE_URL,
        echo=True,  # Set to False after verifying the SQL
    )

    Base.metadata.create_all(engine)

    print("Database created successfully.")
    print("Tables:")

    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")


def get_session() -> Session:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
    )

    return Session(engine)

def get_connection():
    engine = create_engine(
        DATABASE_URL,
        echo=False,
    )
    return engine.connect()


if __name__ == "__main__":
    print("Database create")
    #create_database()
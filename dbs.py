from sqlalchemy import (BigInteger, Column, DateTime, Integer, PickleType,
                        String, func)

from utility import Base, engine, inspector


class Games(Base):
    __tablename__ = "Games"
    index = Column(Integer, primary_key=True, autoincrement=True)
    white_id = Column(BigInteger)
    black_id = Column(BigInteger)
    server_id = Column(BigInteger)
    moves = Column(PickleType)
    start_time = Column(DateTime(timezone=True))
    result = Column(String)


class Playing(Base):
    __tablename__ = "Playing"
    index = Column(Integer, primary_key=True, autoincrement=True)
    white_id = Column(BigInteger)
    black_id = Column(BigInteger)
    message_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    start_time = Column(
        DateTime(timezone=True), default=func.now()
    )  # func.now() adds timestamp when new row is created
    movenum = Column(BigInteger)
    board = Column(PickleType)
    lastmove_time = Column(
        DateTime(timezone=True), onupdate=func.now()
    )  # updates timestamp whenever row is updated


class Solving(Base):
    __tablename__ = "Solving"

    index = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger)
    message_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    board = Column(PickleType)
    movelist = Column(PickleType)
    level = Column(String)
    # lastmove_time = Column(DateTime(timezone=True), onupdate=func.now()) #updates timestamp whenever row is updated


class Solved(Base):
    __tablename__ = "Solved"

    index = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger)
    server_id = Column(BigInteger)
    easy = Column(BigInteger)
    medium = Column(BigInteger)
    hard = Column(BigInteger)
    score = Column(BigInteger)


class Viewing(Base):
    __tablename__ = "Viewing"

    index = Column(Integer, primary_key=True, autoincrement=True)
    embed_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    movenum = Column(BigInteger)
    board = Column(PickleType)
    moves = Column(PickleType)


if not inspector.has_table(Games.__tablename__):
    Games.__table__.create(bind=engine)
if not inspector.has_table(Playing.__tablename__):
    Playing.__table__.create(bind=engine)
if not inspector.has_table(Solved.__tablename__):
    Solved.__table__.create(bind=engine)
if not inspector.has_table(Solving.__tablename__):
    Solving.__table__.create(bind=engine)
if not inspector.has_table(Viewing.__tablename__):
    Viewing.__table__.create(bind=engine)

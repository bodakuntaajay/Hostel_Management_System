import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

# The base for our SQLAlchemy models
Base = declarative_base()

# The database URL for PostgreSQL will be provided by an environment variable.
# For local development, we fall back to SQLite.
database_url = os.environ.get('DATABASE_URL', 'sqlite:///database.db')

# For SQLAlchemy, we modify the database URL if it's the one provided by Heroku,
# which uses a slightly different format.
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(database_url)

class Admin(Base):
    """Admin user for the application."""
    __tablename__ = 'admins'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(128), nullable=False)

class Block(Base):
    """Represents a block in the hostel."""
    __tablename__ = 'blocks'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    rooms = relationship('Room', back_populates='block', cascade='all, delete-orphan')

class Room(Base):
    """Represents a room within a block."""
    __tablename__ = 'rooms'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    bed_count = Column(Integer, default=0)
    block_id = Column(Integer, ForeignKey('blocks.id'))
    block = relationship('Block', back_populates='rooms')
    beds = relationship('Bed', back_populates='room', cascade='all, delete-orphan')

class Person(Base):
    """Represents a person staying in a bed."""
    __tablename__ = 'persons'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    aadhar = Column(String(16), nullable=False, unique=True)
    joining_date = Column(Date, nullable=False)
    leaving_date = Column(Date, nullable=True)
    payments = relationship('Payment', back_populates='person', cascade='all, delete-orphan')
    bed = relationship('Bed', back_populates='person', uselist=False)

class Bed(Base):
    """Represents a single bed within a room."""
    __tablename__ = 'beds'
    id = Column(Integer, primary_key=True)
    bed_number = Column(Integer, nullable=False)
    is_occupied = Column(Boolean, default=False)
    room_id = Column(Integer, ForeignKey('rooms.id'))
    room = relationship('Room', back_populates='beds')
    person_id = Column(Integer, ForeignKey('persons.id'), unique=True, nullable=True)
    person = relationship('Person', back_populates='bed', uselist=False)

class Payment(Base):
    """Represents a monthly payment for a person."""
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey('persons.id'))
    month = Column(String(20), nullable=False)
    status = Column(String(20), default='pending')  # 'done' or 'pending'
    eb_amount = Column(Integer, default=0)
    person = relationship('Person', back_populates='payments')

class Worker(Base):
    """Represents a staff member."""
    __tablename__ = 'workers'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    mobile = Column(String(15), nullable=False)
    gender = Column(String(10), nullable=False)

def create_tables():
    """
    Creates all tables defined in the models.
    This function should be run once to set up the database.
    """
    print("Creating database tables...")
    Base.metadata.create_all(engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    create_tables()

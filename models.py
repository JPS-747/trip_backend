from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Client(Base):
    __tablename__ = 'clients'
    client = Column(String, primary_key=True)
    distanceFromOffice = Column(Float)
    fullAddress = Column(Text)
    isDisabled = Column(Boolean, default=False)
    phoneNumber = Column(String)
    email = Column(String)
    contactPerson = Column(String)
    city = Column(String)
    trips = relationship('Trip', back_populates='client_rel', cascade="all, delete-orphan")

class Vehicle(Base):
    __tablename__ = 'vehicles'
    regNumber = Column(String, primary_key=True)
    make = Column(String)
    model = Column(String)
    year = Column(Integer)
    kmPerLiter = Column(Float)
    currentOdometer = Column(Float, default=0)
    ratePerKm = Column(Float, default=0)
    isDisabled = Column(Boolean, default=False)
    trips = relationship('Trip', back_populates='vehicle_rel', cascade="all, delete-orphan")

class PublicHoliday(Base):
    __tablename__ = 'public_holidays'
    id = Column(Integer, primary_key=True, autoincrement=True)
    country = Column(String)
    year = Column(Integer)
    date = Column(String)
    name = Column(String)

class Setting(Base):
    __tablename__ = 'settings'
    key = Column(String, primary_key=True)
    value = Column(Text)

class Trip(Base):
    __tablename__ = 'trips'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String)
    client = Column(String, ForeignKey('clients.client'))
    city = Column(String)
    distanceKm = Column(Float)
    totalDistanceKm = Column(Float)
    tripType = Column(Integer)
    isPrivateTrip = Column(Boolean, default=False)
    vehicleRegNumber = Column(String, ForeignKey('vehicles.regNumber'))
    client_rel = relationship('Client', back_populates='trips')
    vehicle_rel = relationship('Vehicle', back_populates='trips')

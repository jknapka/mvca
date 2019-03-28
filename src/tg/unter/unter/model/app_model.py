# -*- coding: utf-8 -*-
"""Additional model classes supporting the Unter app."""
from sqlalchemy import *
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Integer, Unicode, DateTime, LargeBinary
from sqlalchemy.orm import relationship, backref

from unter.model import DeclarativeBase, metadata, DBSession


class VolunteerInfo(DeclarativeBase):
    __tablename__ = 'volunteer_info'

    viid = Column(Integer, primary_key=True)
    description = Column(Unicode(255), nullable=False)
    phone = Column(Unicode(32),nullable=True)

    # TO DO: track volunteer locations to enable drive-time
    # estimation. (Use a separate table.)

    user_id = Column(Integer, ForeignKey('tg_user.user_id'), index=True)
    user = relationship('User', uselist=False,
                        backref=backref('volunteer_info',
                                        cascade='all, delete-orphan'))

class VolunteerAvailability(DeclarativeBase):
    __tablename__ = 'volunteer_availability'

    vaid = Column(Integer, primary_key=True)

    # Bitmask of days of week of availability, Sunday=bit 0.
    days_of_week = Column(Integer,nullable=False)

    # Start and end times of availability interval in minutes-
    # past-midnight.
    start_time = Column(Integer,nullable=False)
    end_time = Column(Integer,nullable=False)

    user_id = Column(Integer, ForeignKey('tg_user.user_id'), index=True)
    user = relationship('User', uselist=False,
                        backref=backref('volunteer_availability',
                                        cascade='all, delete-orphan'))
class NeedEvent(DeclarativeBase):
    '''
    Indicate the need for a service.
    This may need to be normalized better.
    '''
    __tablename__ = 'need_event'

    neid = Column(Integer,primary_key=True)

    # This can just be a Unix time.
    date_of_need = Column(Integer,nullable=False)

    # Type of need:
    # 0 == airport
    # 1 == bus station
    # 2 == interpreter
    # ??
    ev_type = Column(Integer,nullable=False)

    # Date on which action is needed.
    date_of_need = Column(Integer,nullable=False)

    # Time of pickup for delivery to transit point, or at which
    # an interpreter is required, in minutes-past-midnight.
    time_of_need = Column(Integer,nullable=False)

    # Estimated duration (minutes).
    duration = Column(Integer,nullable=False)

    # Number of volunteers needed.
    volunteer_count = Column(Integer,nullable=False,default=1)

    # Number of individuals to be served.
    affected_persons = Column(Integer,nullable=False,default=1)

    # Free-form notes - indicate number of individuals, names,
    # etc. We DO NOT want to force users to spend a lot of time
    # entering permanent records for individuals in need of
    # services. This is the only place where we'll track
    # service recipients.
    notes = Column(Unicode(2048),nullable=False)

class VolunteerResponse(DeclarativeBase):
    '''
    When a volunteer indicates they will respond to a need request,
    an entry is made here.
    '''
    __tablename__ = 'volunteer_response'

    vrid = Column(Integer,primary_key=True)

    # The volunteer responding to the event.    
    user_id = Column(Integer,ForeignKey('tg_user.user_id'),nullable=False)
    user = relationship('User', uselist=False,
                        backref=backref('volunteer_response',
                                        cascade='all, delete-orphan'))

    # The event being served by this volunteer.
    neid = Column(Integer,ForeignKey('need_event.neid'),nullable=False)

__all__ = ['VolunteerInfo','VolunteerAvailability','NeedEvent','VolunteerResponse']


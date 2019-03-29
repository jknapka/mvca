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
    description = Column(Unicode(2048), nullable=False)
    phone = Column(Unicode(32),nullable=True)
    text_alerts_ok = Column(Integer,nullable=True,default=1)
    zipcode = Column(Unicode(5),nullable=True,default='')

    user_id = Column(Integer, ForeignKey('tg_user.user_id'), index=True)
    user = relationship('User', uselist=False,
                        backref=backref('volunteer_info',
                                        cascade='all, delete-orphan'))

class VolunteerAvailability(DeclarativeBase):
    __tablename__ = 'volunteer_availability'

    vaid = Column(Integer, primary_key=True)

    dow_sunday = Column(Integer,nullable=False,default=0)
    dow_monday = Column(Integer,nullable=False,default=0)
    dow_tuesday = Column(Integer,nullable=False,default=0)
    dow_wednesday = Column(Integer,nullable=False,default=0)
    dow_thursday = Column(Integer,nullable=False,default=0)
    dow_friday = Column(Integer,nullable=False,default=0)
    dow_saturday = Column(Integer,nullable=False,default=0)

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

    # Type of need:
    # 0 == airport
    # 1 == bus station
    # 2 == interpreter
    # ??
    ev_type = Column(Integer,nullable=False)

    # Date on which action is needed. Unix time.
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

    # If non-null and non-zero, this event has been
    # cancelled.
    #cancelled = Column(Integer,nullable=True)

    #responses = relationship('VolunteerResponse',back_populates='need_event')

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
    #need_event = relationship('NeedEvent',uselist=False,
    #                    backref=backref('need_event',
    #                                    cascade='all, delete-orphan'))

__all__ = ['VolunteerInfo','VolunteerAvailability','NeedEvent','VolunteerResponse']


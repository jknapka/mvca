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
    phone = Column(Unicode(32),nullable=False,default='')
    text_alerts_ok = Column(Integer,nullable=False,default=1)
    zipcode = Column(Unicode(5),nullable=False,default='')

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

    EV_TYPE_AIRPORT = 0
    EV_TYPE_BUS = 1
    EV_TYPE_INTERPRETER = 2

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

    # Location to perform service (pick-up point, etc.)
    location = Column(Unicode(255),nullable=False,default='Unspecified')

    # Free-form notes - indicate number of individuals, names,
    # etc. We DO NOT want to force users to spend a lot of time
    # entering permanent records for individuals in need of
    # services. Among other things that could be dangerous for
    # the people being served. This is the only place where we'll
    # track service recipients.
    notes = Column(Unicode(2048),nullable=False,default='')

    # If non-null and non-zero, this event has been
    # cancelled.
    cancelled = Column(Integer,nullable=False,default=0)

    # Non-null and non-zero if the event is complete.
    complete = Column(Integer,nullable=False,default=0)

    # Last time at which alerts for this event were sent.
    last_alert_time = Column(Integer,nullable=False,default=0)

    created_by_id = Column(Integer,ForeignKey('tg_user.user_id'),nullable=False)
    created_by = relationship('User', uselist=False,
                        backref=backref('need_event',
                                        cascade='all, delete-orphan'))

    responses = relationship('VolunteerResponse')
    refusers = relationship('VolunteerDecommitment')

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
    need_event = relationship('NeedEvent',uselist=False,
                        backref=backref('event_response',
                                        cascade='all, delete-orphan'))

class VolunteerDecommitment(DeclarativeBase):
    '''
    When a volunteer de-commits from an event, we erase the
    corresponding volunteer_response row and add a row here.
    This permits the app code to be much cleaner than if
    we carry a "decommit" flag in volunteer_response.
    '''
    __tablename__ = "volunteer_decommitment"

    vrid = Column(Integer,primary_key=True)

    # The volunteer NOT responding to the event.    
    user_id = Column(Integer,ForeignKey('tg_user.user_id'),nullable=False)
    user = relationship('User', uselist=False,
                        backref=backref('volunteer_decommitment',
                                        cascade='all, delete-orphan'))

    # The event NOT being served by this volunteer.
    neid = Column(Integer,ForeignKey('need_event.neid'),nullable=False)
    need_event = relationship('NeedEvent',uselist=False,
                        backref=backref('decommitted_event',
                                        cascade='all, delete-orphan'))

class AlertUUID(DeclarativeBase):
    '''
    When sending an alert, we embed a UUID in the response link
    sent with the alert. The UUID is a hard-to-guess token
    that hides the user_id and neid being responded to.
    Those associations are stored in this table.
    '''
    __tablename__ = "alert_uuid"

    auid = Column(Integer,primary_key=True)

    # The volunteer to whom the alert was sent.
    user_id = Column(Integer,ForeignKey('tg_user.user_id'),nullable=False)
    user = relationship('User', uselist=False,
                        backref=backref('user_alerts',
                                        cascade='all, delete-orphan'))

    # The event for which the alert was sent.
    neid = Column(Integer,ForeignKey('need_event.neid'),nullable=False)
    need_event = relationship('NeedEvent',uselist=False,
                        backref=backref('event_alerts',
                                        cascade='all, delete-orphan'))

    # The UUID generated for this user/event combination.
    uuid = Column(String(128),nullable=False,index=True)

class PasswordUUID(DeclarativeBase):
    '''
    This table stores UUIDs generated for password reset actions.
    '''
    __tablename__ = "password_reset"

    prid = Column(Integer,primary_key=True)

    user_id = Column(Integer,ForeignKey('tg_user.user_id'),nullable=False)
    user = relationship('User', uselist=False,
            backref=backref('user_password_resets',
                cascade='all, delete-orphan'))

    uuid = Column(String(128),nullable=False)

    create_time = Column(Integer,nullable=False)

__all__ = ['VolunteerInfo','VolunteerAvailability','NeedEvent','VolunteerResponse','VolunteerDecommitment',
        'AlertUUID','PasswordUUID']


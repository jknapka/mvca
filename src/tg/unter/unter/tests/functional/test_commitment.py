'''
Test that we can commit and de-commit volunteers from events.
'''
import sqlalchemy as sql
import sqlalchemy.orm as orm
import transaction
import unter.model as model
import unter.controllers.need as need
import unter.controllers.alerts as alerts
import datetime as dt
import sys

from unter.tests import TestController

from nose.tools import ok_, eq_

class TestCommitment(TestController):

    def setUp(self):
        super().setUp()
        try:
            self.setupDB()
        except:
            transaction.abort()
        else:
            transaction.commit()

    def test_decommit(self):
        '''
        Check that a user can de-commit from an event to which
        they have responded.
        '''
        # Check that the commitment exists.
        u = model.DBSession.query(model.User).filter_by(user_name="testy").first()
        ok_(u is not None)
        ev = model.DBSession.query(model.NeedEvent).filter_by(notes="Test event").first()
        ok_(ev is not None)
        vcom = model.DBSession.query(model.VolunteerResponse).filter_by(user=u).filter_by(need_event=ev).first()
        ok_(vcom is not None)

        # Decommit.
        try:
            need.decommit_volunteer(model.DBSession,vcom=vcom)
        except:
            transaction.abort()
            ok_(False,"TRANSACTION ABORTED: {}".format(sys.exc_info()))
        else:
            transaction.commit()

        # Check that the response row is gone, and a decommit row exists.
        u = model.DBSession.query(model.User).filter_by(user_name="testy").first()
        ok_(u is not None)
        ev = model.DBSession.query(model.NeedEvent).filter_by(notes="Test event").first()
        ok_(ev is not None)
        vcom = model.DBSession.query(model.VolunteerResponse).filter_by(user=u).filter_by(need_event=ev).first()
        ok_(vcom is None)
        vdecom = model.DBSession.query(model.VolunteerDecommitment).filter_by(user=u).filter_by(need_event=ev).first()
        ok_(vdecom is not None)

    def test_decommit_with_no_response(self):
        '''
        Check that a user can decommit from an event without
        first responding to it (eg to say: "While I would normally
        be available to serve this event, for contingent reasons
        I cannot in fact do so").
        '''
        # Check that neither a response nor a decommit exists.
        u = model.DBSession.query(model.User).filter_by(user_name="testy").first()
        ok_(u is not None)
        ev = model.DBSession.query(model.NeedEvent).filter_by(notes="Test event 2").first()
        ok_(ev is not None)
        vcom = model.DBSession.query(model.VolunteerResponse).filter_by(user=u).filter_by(need_event=ev).first()
        ok_(vcom is None)
        vdecom = model.DBSession.query(model.VolunteerDecommitment).filter_by(user=u).filter_by(need_event=ev).first()
        ok_(vdecom is None)

        # Decommit.
        try:
            need.decommit_volunteer(model.DBSession,user=u,ev=ev)
        except:
            transaction.abort()
            ok_(False,"TRANSACTION ABORTED: {}".format(sys.exc_info()))
        else:
            transaction.commit()

        # Check that there is still no response row, and a decommit row exists.
        u = model.DBSession.query(model.User).filter_by(user_name="testy").first()
        ok_(u is not None)
        ev = model.DBSession.query(model.NeedEvent).filter_by(notes="Test event 2").first()
        ok_(ev is not None)
        vcom = model.DBSession.query(model.VolunteerResponse).filter_by(user=u).filter_by(need_event=ev).first()
        ok_(vcom is None)
        vdecom = model.DBSession.query(model.VolunteerDecommitment).filter_by(user=u).filter_by(need_event=ev).first()
        ok_(vdecom is not None)

    def setupDB(self):
        try:
            session = model.DBSession

            u = model.User(user_name="testy",email_address="test@test.test")
            vi = model.VolunteerInfo(phone="1234567890",description="Test user")
            u.vinfo = vi
            session.add(u)
            session.add(vi)

            # A need to which u will respond.
            e = model.NeedEvent()
            e.ev_type = 0
            e.duration=70
            e.created_by = u
            e.date_of_need = dt.date.today() + dt.timedelta(days=1)
            e.time_of_need = 10*60
            e.volunteer_count = 2
            e.affected_persons = 2
            e.notes = "Test event"
            e.location = "Nowhere"
            session.add(e)

            # u's response.
            vcom = model.VolunteerResponse()
            vcom.user = u
            vcom.need_event = e
            session.add(vcom)
            
            # A need with no volunteer response.
            e = model.NeedEvent()
            e.ev_type = 0
            e.duration=70
            e.created_by = u
            e.date_of_need = dt.date.today() + dt.timedelta(days=2)
            e.time_of_need = 10*60
            e.volunteer_count = 1
            e.affected_persons = 3
            e.notes = "Test event 2"
            e.location = "Somewhere"
            session.add(e)

            session.flush()
        except:
            transaction.abort()
        else:
            transaction.commit()

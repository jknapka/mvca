'''
Test that we can commit and de-commit volunteers from events.
'''
import sqlalchemy as sql
import sqlalchemy.orm as orm
import transaction
import logging
import unter.model as model
import unter.controllers.need as need
import unter.controllers.alerts as alerts
import datetime as dt
import sys
import traceback

from unter.tests import TestController

from nose.tools import ok_, eq_

class TestCommitment(TestController):

    def setUp(self):
        super().setUp()
        self.setupDB()

    def test_decommit(self):
        ''' A user can de-commit from an event to which they have responded.  '''
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
            import traceback
            from io import StringIO
            einfo = sys.exc_info()
            sio = StringIO()
            traceback.print_tb(einfo[2],file=sio)
            ok_(False,"TRANSACTION ABORTED: {} {} {}".format(einfo[0],einfo[1],sio.getvalue()))
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
        ''' A user can decommit from an event without first responding to it. '''
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

            u = model.User(user_name="testy",email_address="test@test.test",
                            phone="1234567890",description="Test user")
            session.add(u)

            # A need to which u will respond.
            e = model.NeedEvent()
            e.etid = model.NeedEvent.EV_TYPE_AIRPORT
            e.duration=70
            e.created_by = u
            e.date_of_need = int((dt.datetime.now() + dt.timedelta(days=1)).timestamp())
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
            e.etid = model.NeedEvent.EV_TYPE_AIRPORT
            e.duration=70
            e.created_by = u
            e.date_of_need = int((dt.datetime.now() + dt.timedelta(days=1)).timestamp())
            e.time_of_need = 10*60
            e.volunteer_count = 1
            e.affected_persons = 3
            e.notes = "Test event 2"
            e.location = "Somewhere"
            session.add(e)

            session.flush()
        except:
            ei = sys.exc_info()
            from io import StringIO
            sio = StringIO()
            traceback.print_tb(ei[2],file=sio)
            logging.getLogger('unter.test').error('ABORTING TRANSACTION: {} {}\n{}'.\
                    format(ei[0],ei[1],sio.getvalue()))
            print(sio.getvalue())
            transaction.abort()
            transaction.abort()
        else:
            transaction.commit()

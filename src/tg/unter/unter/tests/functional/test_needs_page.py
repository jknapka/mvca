'''
Test the /need_events URL.
'''
import sqlalchemy as sql
import sqlalchemy.orm as orm
import transaction
import unter.model as model
import unter.controllers.need as need
import unter.controllers.alerts as alerts
import datetime as dt

from tg import expose, flash, require, url, lurl

from unter.tests import TestController

from nose.tools import ok_, eq_

from bs4 import BeautifulSoup as bsoup

from io import StringIO

import logging

class TestNeedEventsPage(TestController):

    def setUp(self):
        super().setUp()
        try:
            self.setupDB()
        except:
            import sys
            print("ABORTING TRANSACTION: {}".format(sys.exc_info()),file=sys.stderr)
            transaction.abort()
        else:
            transaction.commit()

    def test_0_alertAllLink(self):
        ''' The "Send event alerts" link appears.  '''
        env = {'REMOTE_USER':'carla'}
        resp = self.app.get('/need_events?complete=0',extra_environ=env,
                status=200)
        ok_('Send alerts for all' in resp.text,resp.text)

    def test_1_alerts1(self):
        ''' We alert only non-fully-staffed events. '''
        try:
            self.createResponse('veronica','Veronica only bus 1')
            self.createResponse('velma','Veronica or Velma airport')
        except:
            transaction.abort()
        else:
            transaction.commit()

        env = {'REMOTE_USER':'carla'}
        resp = self.app.get('/check_events',extra_environ=env,
                status=302)

        def getUuidForEventFromUUIDTable(neid):
            auuid = model.DBSession.query(model.AlertUUID).filter_by(neid=neid).first()
            if auuid is None:
                return None
            return auuid.uuid

        # We should have alerted for all events except
        # "Veronica only bus 1" and "... bus 2" (the second
        # because those two events overlap and Veronica
        # cannot do both).
        alertLog = self.getAlertLog()
        evs = model.DBSession.query(model.NeedEvent).all()
        for ev in evs:
            if ev.notes in ["Veronica only bus 1","Veronica only bus 2"]:
                # There should not be a UUID entry for this event.
                uuid = getUuidForEventFromUUIDTable(ev.neid)
                ok_(uuid is None)
            else:
                # There should be a UUID for this event and it should
                # appear in the alert texts.
                uuid = getUuidForEventFromUUIDTable(ev.neid)
                ok_('?uuid={}'.format(uuid) in alertLog,alertLog)

    def setupDB(self):
        self.createCoordinatorCarla()
        self.createVolunteers()
        self.createAvailabilities()
        self.createEvents()

        # Make "Veronica or Velma airport" need 2 volunteers.
        ev = model.DBSession.query(model.NeedEvent).\
                filter_by(notes="Veronica or Velma airport").first()
        ev.volunteer_count = 2

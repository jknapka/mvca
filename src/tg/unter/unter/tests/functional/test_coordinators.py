'''
Test the /coord_page URL.
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

# Alerter stub that captures alert information for tests.
TEST_ALERT_OUTPUT = StringIO()

class TestCoordPage(TestController):

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

    def test_0_lastAlertTimesInCoordPage(self):
        ''' "Last alert" times appear for events in coord page. '''
        resp = self.app.get('/coord_page',extra_environ={'REMOTE_USER':'carla'},status=200)
        ok_('Last alert' in resp.text,resp.text)

        zup = bsoup(resp.text,features="html.parser")
        td = str(zup.find(id='alert-time-ev-1'))
        ok_(dt.datetime.fromtimestamp(0).ctime() in td,td)

    def test_1_lastAlertTimeUpdatesOnAlert(self):
        ''' The "Last alert" time updates when an alert is sent. '''
        nev = model.DBSession.query(model.NeedEvent).first()

        # With an empty volunteers list, this will update the last
        # alert time without actually alerting anyone.
        try:
            alerts.sendAlerts([],nev)
        except:
            transaction.abort()
        else:
            transaction.commit()
        now = dt.datetime.now()

        # Check that the new update time is reflected
        # in the page results.
        resp = self.app.get('/coord_page',extra_environ={'REMOTE_USER':'carla'},status=200)

        zup = bsoup(resp.text,features="html.parser")
        td = str(zup.find(id='alert-time-ev-1'))
        ok_(now.ctime() in td,td)

    def test_2_alertLinksInEvents(self):
        ''' "Send alert" links appear in the event table. '''
        resp = self.app.get('/coord_page',extra_environ={'REMOTE_USER':'carla'},status=200)
        zup = bsoup(resp.text,features="html.parser")
        td = str(zup.find(id='alert-time-ev-1'))
        ok_('href="/send_alert?neid=1"' in td,td)

    def test_3_alerts1(self):
        '''
        Appropriate people are alerted when we send alerts.
        '''
        nev = model.DBSession.query(model.NeedEvent).filter_by(\
                notes="Veronica or Velma airport").first()
        # No commitments.
        env = {"REMOTE_USER":'carla'}
        resp = self.app.get("/send_alert?neid={}".format(nev.neid),
                extra_environ=env,status=302)

        # Check that Velma's and Veronica's phone numbers
        # appear in the alert log.
        alertLog = self.getAlertLog()
        ok_('9150010002' in alertLog,alertLog)
        ok_('9150010003' in alertLog,alertLog)
        ok_('Call Carla 9150010001' in alertLog,alertLog)

    def test_4_availableVolunteers(self):
        ''' We correctly identify volunteers available to serve an event. '''
        nev = model.DBSession.query(model.NeedEvent).filter_by(\
                notes="Veronica or Velma airport").first()
        # No commitments.
        env = {"REMOTE_USER":'carla'}
        resp = self.app.get("/event_details?neid={}".format(nev.neid),
                extra_environ=env,status=200)

        zup = bsoup(resp.text,features="html.parser")
        vols_avail = str(zup.find(id="volunteers-available"))
        ok_("Veronica" in vols_avail,vols_avail)
        ok_("Velma" in vols_avail,vols_avail)

    def test_5_committedVolunteers(self):
        ''' We correctly identify volunteers committed to serve an event. '''
        # Commit Velma.
        try:
            self.createResponse('velma','Veronica or Velma airport')
        except:
            import sys
            logging.getLogger('unter.test').error("ABORTING TRANSACTION: {}".format(sys.exc_info()))
            transaction.abort()
        else:
            transaction.commit()

        nev = model.DBSession.query(model.NeedEvent).filter_by(\
                notes="Veronica or Velma airport").first()

        env = {"REMOTE_USER":'carla'}
        resp = self.app.get("/event_details?neid={}".format(nev.neid),
                extra_environ=env,status=200)

        zup = bsoup(resp.text,features="html.parser")
        vols_committed = str(zup.find(id="volunteers-committed"))
        ok_("Veronica" not in vols_committed,vols_committed)
        ok_("Velma" in vols_committed,vols_committed)

        vols_avail = str(zup.find(id="volunteers-available"))
        ok_("Veronica" in vols_avail,vols_avail)
        ok_("Velma" not in vols_avail,vols_avail)

    def setupDB(self):
        '''
        DB entities needed for these tests:

        1) A coordinator.
        2) A volunteer or two.
        3) Some events.
        4) At least one volunteer availability for an event.
        '''
        #self.setupNeedEventEntities()
        self.createCoordinatorCarla()
        self.createVolunteers()
        self.createAvailabilities()
        self.createEvents()

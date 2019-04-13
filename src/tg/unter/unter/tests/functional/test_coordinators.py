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

class TestCoordPage(TestController):

    def setUp(self):
        super().setUp()
        try:
            self.setupDB()
        except:
            transaction.abort()
        else:
            transaction.commit()

    def test_0_lastAlertTimesInCoordPage(self):
        resp = self.app.get('/coord_page',extra_environ={'REMOTE_USER':'carla'},status=200)
        ok_('Last alert sent' in resp.text,resp.text)

        zup = bsoup(resp.text,features="html.parser")
        td = str(zup.find(id='alert-time-neid-1'))
        ok_(dt.datetime.fromtimestamp(0).ctime() in td,td)

    def test_1_lastAlertTimeUpdatesOnAlert(self):
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
        td = str(zup.find(id='alert-time-neid-1'))
        ok_(now.ctime() in td,td)

    def test_2_alertLinksInEvents(self):
        resp = self.app.get('/coord_page',extra_environ={'REMOTE_USER':'carla'},status=200)
        zup = bsoup(resp.text,features="html.parser")
        td = str(zup.find(id='alert-time-neid-1'))
        ok_('href="/send_alert?neid=1"' in td,td)

    def setupDB(self):
        '''
        DB entities needed for these tests:

        1) A coordinator.
        2) A volunteer or two.
        3) Some events.
        4) At least one volunteer availability for an event.
        '''
        self.setupNeedEventEntities()

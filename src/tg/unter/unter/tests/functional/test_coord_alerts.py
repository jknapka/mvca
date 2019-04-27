'''
Test that coordinators receive alerts under appropriate conditions.
'''
import sqlalchemy as sql
import sqlalchemy.orm as orm
import transaction
import traceback
import datetime as dt
import re

import unter.model as model
import unter.controllers.need as need
import unter.controllers.alerts as alerts

from tg import expose, flash, require, url, lurl

from unter.tests import TestController

from nose.tools import ok_, eq_

from bs4 import BeautifulSoup as bsoup

from io import StringIO

import logging

import unter.model as model
import unter.controllers.alerts as alerts
import unter.controllers.need as need

class TestCoordinatorAlerts(TestController):

    def setUp(self):
        super().setUp()

        self.createCoordinatorCarla()
        self.createVolunteers()

        # Create a test event.
        self.createEvent(created_by=self.getUser(model.DBSession,'carla'),
                location='test location',
                notes='test event',
                time_of_need=8*60)

        transaction.commit()

        # Disable email alerts and enable SMS ones.
        alerts.EMAIL_ENABLED = False
        alerts.SMS_ENABLED = True

    def test_0_decommitCommittedVolAlertsCoord(self):
        ''' A volunteer leaving an event they've committed to alerts the coordinator. '''
        # Veronica commits.
        env = {'REMOTE_USER':'veronica'}
        self.app.get('/respond?neid=1',extra_environ=env,status=302)

        # Alerts blah blah. Carla's phone number should NOT appear
        # in the alert log. (UNLESS we later decide to alert coordinators
        # when volunteers respond to their events!)
        alerts = self.getAlertLog()
        ok_('9150010001' not in alerts,alerts)
        # Veronica's number should though.
        v = self.getUser(model.DBSession,'veronica')
        ok_(v.vinfo.phone in alerts,alerts)
        self.resetAlertLog()

        # Veronica decommits.
        self.app.get('/decommit?neid=1',extra_environ=env,status=302)

        # Now Carla should have an alert that Veronica bailed.
        alerts = self.getAlertLog()
        ok_('9150010001' in alerts,alerts)
        ok_('Veronica cannot serve' in alerts,alerts)

    def test_1_decommitUncommittedVolNoAlert(self):
        ''' A volunteer refusing an event they're not committed to generates no alerts.'''
        env = {'REMOTE_USER':'veronica'}
        self.app.get('/decommit?neid=1',extra_environ=env,status=302)

        # The alert log should be empty.
        alerts = self.getAlertLog()
        eq_('',alerts,alerts)


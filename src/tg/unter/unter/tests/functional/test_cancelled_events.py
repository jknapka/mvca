'''
Test that cancelling events works properly.
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

class TestCancelledEvents(TestController):

    def setUp(self):
        super().setUp()
        self.createCoordinatorCarla()
        self.createVolunteers()
        carla = self.getUser(model.DBSession,'carla')
        self.createEvent(created_by=carla,volunteer_count=2,notes='Test event')
        transaction.commit()

    def test_0_noRepondentsNoAlerts(self):
        env = {'REMOTE_USER':'carla'}
        self.app.get('/cancel_event?neid=1',extra_environ=env,status=302)
        alerts = self.getAlertLog()
        eq_('',alerts,'Unexpectedly sent alerts: {}'.format(alerts))

    def test_1_oneRespondentOneAlert(self):
        # Veronica responds...
        env = {'REMOTE_USER':'veronica'}
        self.app.get('/respond?neid=1',extra_environ=env,status=302)
        alerts = self.getAlertLog()
        v = self.getUser(model.DBSession,'veronica')
        veronicaPhone = v.vinfo.phone
        ok_(veronicaPhone in alerts,'Should have alerted veronica with a "Thank you"')

        # And then the event is cancelled.
        self.resetAlertLog()
        env = {'REMOTE_USER':'carla'}
        self.app.get('/cancel_event?neid=1',extra_environ=env,status=302)
        alerts = self.getAlertLog()
        # We should see a cancellation alert for veronica, but
        # not for velma.
        ok_(veronicaPhone in alerts,'Should have alerted veronica of a cancellation: {}'.\
                format(alerts))
        ok_('has been cancelled' in alerts,'Should have been a cancellation alert: {}'.\
                format(alerts))

    def test_2_twoRespondentsTwoAlerts(self):
        v = self.getUser(model.DBSession,'veronica')
        veronicaPhone = v.vinfo.phone
        v = self.getUser(model.DBSession,'velma')
        velmaPhone = v.vinfo.phone

        # Veronica responds...
        env = {'REMOTE_USER':'veronica'}
        self.app.get('/respond?neid=1',extra_environ=env,status=302)
        alerts = self.getAlertLog()
        ok_(veronicaPhone in alerts,'Should have alerted veronica with a "Thank you": {}'.\
                format(alerts))
        ok_(velmaPhone not in alerts,'Should not have alerted velma: {}'.\
                format(alerts))

        # Velma responds...
        env = {'REMOTE_USER':'velma'}
        self.app.get('/respond?neid=1',extra_environ=env,status=302)
        alerts = self.getAlertLog()
        ok_(velmaPhone in alerts,'Should have alerted velma with a "Thank you": {}'.\
                format(alerts))

        # And then the event is cancelled.
        self.resetAlertLog()
        env = {'REMOTE_USER':'carla'}
        self.app.get('/cancel_event?neid=1',extra_environ=env,status=302)
        alerts = self.getAlertLog()
        # We should see cancellation alerts for veronica and velma.
        ok_(veronicaPhone in alerts,'Should have alerted veronica of a cancellation: {}'.\
                format(alerts))
        ok_(velmaPhone in alerts,'Should have alerted velma of a cancellation: {}'.\
                format(alerts))
        ok_('has been cancelled' in alerts,'Should have been a cancellation alert: {}'.\
                format(alerts))


'''
Test adding and removing available times.
'''
# vim: tabstop=4 softtabstop=4 expandtab shiftwidth=4
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

class TestAvailability(TestController):

    def setUp(self):
        super().setUp()
        self.createCoordinatorCarla()
        self.createVolunteers()
        transaction.commit()

    def test_0_addAvailableTimePageAnonymous(self):
        ''' We cannot load the "Add available time" page when not logged in.'''
        resp = self.app.get('/add_availability_start',status=401)
        # All we care about is that we get an unauthorized response.

    def test_1_addAvailableTimePageWithId(self):
        ''' We can load the "Add available time" page while logged in. '''
        env = {'REMOTE_USER':'veronica'}
        resp = self.app.get('/add_availability_start',status=200,
                extra_environ=env)
        ok_('Indicate a time period and the days' in resp.text,resp.text)

    def test_2_addAvaiableTimeAnonymousFails(self):
        ''' We cannot add an available time when anonymous. '''
        v = model.DBSession.query(model.User).filter_by(user_name='veronica').first()
        v_user_id = v.user_id
        resp = self.app.post('/add_availability_post',status=401,
                params=dict(
                    user_id = v_user_id,
                    start_time = '10:15',
                    end_time = '18:40',
                    dow_sunday = 'true',
                    dow_monday = 'true',
                    dow_tuesday = 'true',
                    dow_wednesday = 'true',
                    dow_thursday = 'true',
                    dow_friday = 'true',
                    dow_saturday = 'false'
                    ))
        # If we're unauthorized, that's what we expect.

    def test_3_addAvailableTime(self):
        ''' A volunteer can add an available time. '''
        env = {'REMOTE_USER':'veronica'}
        v = model.DBSession.query(model.User).filter_by(user_name='veronica').first()
        v_user_id = v.user_id
        resp = self.app.post('/add_availability_post',status=302,
                extra_environ=env,
                params=dict(
                    user_id = v_user_id,
                    start_time='11:10',
                    end_time = '17:23',
                    dow_sunday = 'true',
                    dow_monday = 'true',
                    dow_tuesday = 'true',
                    dow_wednesday = 'true',
                    dow_thursday = 'true',
                    dow_friday = 'true',
                    dow_saturday = 'false'
                    ))

        resp = self.app.get('/volunteer_info',extra_environ=env,status=200)
        ok_('11:10' in resp.text,resp.text)
        ok_('17:23' in resp.text,resp.text)
        ok_('Sun' in resp.text,resp.text)
        ok_('Mon' in resp.text,resp.text)
        ok_('Tue' in resp.text,resp.text)
        ok_('Wed' in resp.text,resp.text)
        ok_('Thu' in resp.text,resp.text)
        ok_('Fri' in resp.text,resp.text)
        ok_('Sat' not in resp.text,resp.text)

    def test_4_removeAvailableTimeAnonymousFails(self):
        ''' An anonymous user can't remove another user's available time. '''
        env = {'REMOTE_USER':'veronica'}
        v = model.DBSession.query(model.User).filter_by(user_name='veronica').first()
        v_user_id = v.user_id
        resp = self.app.post('/add_availability_post',status=302,
                extra_environ=env,
                params=dict(
                    user_id = v_user_id,
                    start_time='11:10',
                    end_time = '17:23',
                    dow_sunday = 'true',
                    dow_monday = 'true',
                    dow_tuesday = 'true',
                    dow_wednesday = 'true',
                    dow_thursday = 'true',
                    dow_friday = 'true',
                    dow_saturday = 'false'
                    ))
        avail = model.DBSession.query(model.VolunteerAvailability).first()
        vaid = avail.vaid

        resp = self.app.get('/remove_availability?vaid={}'.format(vaid),status=401)
        # All we need to know is that we get a 401.

    def test_5_removeAvailableTime(self):
        ''' A user can remove their own available time. '''
        env = {'REMOTE_USER':'veronica'}
        v = model.DBSession.query(model.User).filter_by(user_name='veronica').first()
        v_user_id = v.user_id
        resp = self.app.post('/add_availability_post',status=302,
                extra_environ=env,
                params=dict(
                    user_id = v_user_id,
                    start_time='11:10',
                    end_time = '17:23',
                    dow_sunday = 'true',
                    dow_monday = 'true',
                    dow_tuesday = 'true',
                    dow_wednesday = 'true',
                    dow_thursday = 'true',
                    dow_friday = 'true',
                    dow_saturday = 'false'
                    ))
        avail = model.DBSession.query(model.VolunteerAvailability).first()
        vaid = avail.vaid

        resp = self.app.get('/remove_availability?vaid={}'.format(vaid),status=302,
                extra_environ=env)
        ok_('/volunteer_info' in resp.text,resp.text)

        resp = self.app.get('/volunteer_info',extra_environ=env,status=200)
        ok_('11:10' not in resp.text,resp.text)
        ok_('17:23' not in resp.text,resp.text)
        ok_('Sun' not in resp.text,resp.text)
        ok_('Mon' not in resp.text,resp.text)
        ok_('Tue' not in resp.text,resp.text)
        ok_('Wed' not in resp.text,resp.text)
        ok_('Thu' not in resp.text,resp.text)
        ok_('Fri' not in resp.text,resp.text)
        ok_('Sat' not in resp.text,resp.text)

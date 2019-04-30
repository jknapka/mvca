'''
Test the /all_volunteers URL.
'''
import sqlalchemy as sql
import sqlalchemy.orm as orm
import transaction
import unter.model as model
import unter.controllers.need as need
import unter.controllers.alerts as alerts
import datetime as dt
import logging

from unter.tests import TestController
import unter.controllers.util as util

from nose.tools import ok_, eq_

from bs4 import BeautifulSoup as bsoup

class TestAllVolunteers(TestController):

    def setUp(self):
        super().setUp()
        try:
            util.setupTestUsers()
            util.setupTestAvailabilities()
            util.setupTestEvents()
        except:
            import sys
            util.debugTest("ABORTING TRANSACTION: {}".format(sys.exc_info()))
            transaction.abort()
        else:
            transaction.commit()
            users = model.DBSession.query(model.User).all()
            for u in users:
                logging.getLogger('unter.test').info('Created user: {}'.format(u.user_name))

    def test_0_allVolsPage(self):
        env = {'REMOTE_USER':'carla'}
        resp = self.app.get('/all_volunteers',extra_environ=env,status=200)
        users = model.DBSession.query(model.User).all()
        for u in users:
            perms = [p.permission_name for p in u.permissions]
            if 'respond_to_need' in perms:
                ok_(u.display_name in resp.text,resp.text)
            if 'manage_events' in perms:
                ok_(u.display_name in resp.text,resp.text)

    def test_1_allVolsPageNoAccessForVolunteers(self):
        env = {'REMOTE_USER':'velma'}
        # This should fail with an auth error.
        resp = self.app.get('/all_volunteers',extra_environ=env,status=403)


'''
Test the "Add volunteer" page.
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

class TestAddVolunteer(TestController):

    def setUp(self):
        super().setUp()
        self.createCoordinatorCarla()
        transaction.commit()

    def test_0_anonymousCanLoadAddVolunteerPage(self):
        ''' Anonymous users can add themselves as new volunteers.'''
        resp = self.app.get('/add_volunteer_start',status=200)
        ok_('User Name' in resp.text,resp.text)
        ok_('Display Name' in resp.text,resp.text)

    def test_1_newVolunteerHasNoPrivileges(self):
        ''' Newly-created volunteers created anonymously have no privileges. '''
        resp = self.app.post('/add_volunteer_post',status=302,
                params={
                    'user_name': 'testPerson',
	            'display_name': 'Test Person',
	            'pwd': 'testPwd',
	            'pwd2': 'testPwd',
	            'email': 'test@test.com',
	            'phone': '9150420042',
	            'text_alerts_ok': 'true',
	            'zipcode': '79900',
	            'description': 'Test user'
                    })
        vol = model.DBSession.query(model.User).filter_by(user_name='testPerson').first()
        ok_(vol is not None,"Failed to create the test user")
        perms = vol.permissions
        eq_(0,len(perms),"Test user has permissions: {}".format([p.permission_name for p in vol.permissions]))

    def test_2_coordCanApproveNewVolunteer(self):
        ''' Coordinators can approve new volunteers. '''
        # Create a new volunteer.
        resp = self.app.post('/add_volunteer_post',status=302,
                params={
                    'user_name': 'testPerson',
	            'display_name': 'Test Person',
	            'pwd': 'testPwd',
	            'pwd2': 'testPwd',
	            'email': 'test@test.com',
	            'phone': '9150420042',
	            'text_alerts_ok': 'true',
	            'zipcode': '79900',
	            'description': 'Test user'
                    })
        vol = model.DBSession.query(model.User).filter_by(user_name='testPerson').first()
        vol_id = vol.user_id

        # Try to edit.
        env = {'REMOTE_USER':'carla'}
        resp = self.app.get('/add_volunteer_start?user_id={}'.format(vol_id),
                extra_environ=env,status=200)
        ok_('Activate volunteer' in resp.text,resp.text)

    def test_3_volunteerCreatedByCoordIsPreApproved(self):
        ''' Newly-created volunteers created by coordinators start out activated. '''
        env = {'REMOTE_USER':'carla'}
        resp = self.app.post('/add_volunteer_post',status=302,
                extra_environ=env,
                params={
                    'user_name': 'testPerson',
	            'display_name': 'Test Person',
	            'pwd': 'testPwd',
	            'pwd2': 'testPwd',
	            'email': 'test@test.com',
	            'phone': '9150420042',
	            'text_alerts_ok': 'true',
	            'zipcode': '79900',
	            'description': 'Test user'
                    })
        vol = model.DBSession.query(model.User).filter_by(user_name='testPerson').first()
        ok_(vol is not None,"Failed to create the test user")
        perms = [p.permission_name for p in vol.permissions]
        ok_('respond_to_need' in perms,"Test user has no respond_to_need permission: {}".\
                format(perms))

    def test_4_activatedVolunteersCanBeDeactivated(self):
        ''' Coordinators can deactivate volunteers.'''
        env = {'REMOTE_USER':'carla'}
        resp = self.app.post('/add_volunteer_post',status=302,
                extra_environ=env,
                params={
                    'user_name': 'testPerson',
	            'display_name': 'Test Person',
	            'pwd': 'testPwd',
	            'pwd2': 'testPwd',
	            'email': 'test@test.com',
	            'phone': '9150420042',
	            'text_alerts_ok': 'true',
	            'zipcode': '79900',
	            'description': 'Test user'
                    })
        vol = model.DBSession.query(model.User).filter_by(user_name='testPerson').first()
        resp = self.app.get('/add_volunteer_start?user_id={}'.format(vol.user_id),
                status=200,
                extra_environ=env)
        ok_('Deactivate volunteer' in resp.text,resp.text)

    def test_5_volunteersCanOnlyEditSelf(self):
        ''' Non-activated volunteers can only edit themselves.'''
        resp = self.app.post('/add_volunteer_post',status=302,
                params={
                    'user_name': 'testPerson',
	            'display_name': 'Test Person',
	            'pwd': 'testPwd',
	            'pwd2': 'testPwd',
	            'email': 'test@test.com',
	            'phone': '9150420042',
	            'text_alerts_ok': 'true',
	            'zipcode': '79900',
	            'description': 'Test user'
                    })
        vol = model.DBSession.query(model.User).filter_by(user_name='testPerson').first()
        ok_(vol is not None,"Failed to create the test user")

        env = {'REMOTE_USER':'testPerson'}
        resp = self.app.get('/add_volunteer_start?user_id={}'.format(vol.user_id),
                extra_environ=env, status=200)
        ok_('Delete volunteer account' in resp.text,resp.text)
        ok_('Activate volunteer' not in resp.text,resp.text)
        ok_('Promote volunteer' not in resp.text,resp.text)

        resp = self.app.get('/add_volunteer_start?user_id=3',
                extra_environ=env, status=302)
        ok_('/volunteer_info' in resp.text,resp.text)

    def test_6_activatedVolunteersCanOnlyEditSelf(self):
        ''' Non-managers and non-coordinators can only edit themselves.'''
        env = {'REMOTE_USER':'carla'}
        resp = self.app.post('/add_volunteer_post',status=302,
                extra_environ=env,
                params={
                    'user_name': 'testPerson',
	            'display_name': 'Test Person',
	            'pwd': 'testPwd',
	            'pwd2': 'testPwd',
	            'email': 'test@test.com',
	            'phone': '9150420042',
	            'text_alerts_ok': 'true',
	            'zipcode': '79900',
	            'description': 'Test user'
                    })
        vol = model.DBSession.query(model.User).filter_by(user_name='testPerson').first()
        ok_(vol is not None,"Failed to create the test user")
        perms = [p.permission_name for p in vol.permissions]
        ok_('respond_to_need' in perms,"Test user has no respond_to_need permission: {}".\
                format(perms))

        env = {'REMOTE_USER':'testPerson'}
        resp = self.app.get('/add_volunteer_start?user_id={}'.format(vol.user_id),
                extra_environ=env, status=200)
        ok_('Delete volunteer account' in resp.text,resp.text)
        ok_('Activate volunteer' not in resp.text,resp.text)
        ok_('Promote volunteer' not in resp.text,resp.text)

        resp = self.app.get('/add_volunteer_start?user_id=3',
                extra_environ=env, status=302)
        ok_('/volunteer_info' in resp.text,resp.text)

    def test_7_coordCanEditVol(self):
        ''' A coordinator can edit a volunteer. '''
        env = {'REMOTE_USER':'carla'}
        resp = self.app.post('/add_volunteer_post',status=302,
                params={
                    'user_name': 'testPerson',
	            'display_name': 'Test Person',
	            'pwd': 'testPwd',
	            'pwd2': 'testPwd',
	            'email': 'test@test.com',
	            'phone': '9150420042',
	            'text_alerts_ok': 'true',
	            'zipcode': '79900',
	            'description': 'Test user'
                    })
        vol = model.DBSession.query(model.User).filter_by(user_name='testPerson').first()
        ok_(vol is not None,"Failed to create the test user")
        vol_id = vol.user_id

        resp = self.app.get('/add_volunteer_start?user_id={}'.format(vol_id),
                extra_environ=env, status=200)
        ok_('Activate volunteer' in resp.text,resp.text)
        ok_('Delete volunteer account' in resp.text,resp.text)

        resp = self.app.get('/add_volunteer_start?user_id={}'.format(vol_id),
                extra_environ=env, status=200)

    def test_8_managerCanEditVol(self):
        ''' A manager can edit a volunteer. '''
        env = {'REMOTE_USER':'manager'}
        resp = self.app.post('/add_volunteer_post',status=302,
                params={
                    'user_name': 'testPerson',
	            'display_name': 'Test Person',
	            'pwd': 'testPwd',
	            'pwd2': 'testPwd',
	            'email': 'test@test.com',
	            'phone': '9150420042',
	            'text_alerts_ok': 'true',
	            'zipcode': '79900',
	            'description': 'Test user'
                    })
        vol = model.DBSession.query(model.User).filter_by(user_name='testPerson').first()
        ok_(vol is not None,"Failed to create the test user")
        vol_id = vol.user_id

        resp = self.app.get('/add_volunteer_start?user_id={}'.format(vol_id),
                extra_environ=env, status=200)
        ok_('Activate volunteer' in resp.text,resp.text)
        ok_('Delete volunteer account' in resp.text,resp.text)

        resp = self.app.get('/add_volunteer_start?user_id={}'.format(vol_id),
                extra_environ=env, status=200)

    def test_9_activationWorks(self):
        ''' A coordinator can activate a volunteer. '''
        resp = self.app.post('/add_volunteer_post',status=302,
                params={
                    'user_name': 'testPerson',
	            'display_name': 'Test Person',
	            'pwd': 'testPwd',
	            'pwd2': 'testPwd',
	            'email': 'test@test.com',
	            'phone': '9150420042',
	            'text_alerts_ok': 'true',
	            'zipcode': '79900',
	            'description': 'Test user'
                    })
        vol = model.DBSession.query(model.User).filter_by(user_name='testPerson').first()
        ok_(vol is not None,"Failed to create the test user")
        perms = [p.permission_name for p in vol.permissions]
        ok_('respond_to_need' not in perms,perms)
        vol_id = vol.user_id

        env = {'REMOTE_USER':'carla'}
        resp = self.app.get('/activate_volunteer?user_id={}'.format(vol_id),
                extra_environ=env, status=302)

        vol = model.DBSession.query(model.User).filter_by(user_name='testPerson').first()
        perms = [p.permission_name for p in vol.permissions]
        ok_('respond_to_need' in perms,perms)

    def test_10_deactivationWorks(self):
        ''' A coordinator can deactivate a volunteer. '''
        env = {'REMOTE_USER':'carla'}
        resp = self.app.post('/add_volunteer_post',status=302,
                extra_environ=env,
                params={
                    'user_name': 'testPerson',
	            'display_name': 'Test Person',
	            'pwd': 'testPwd',
	            'pwd2': 'testPwd',
	            'email': 'test@test.com',
	            'phone': '9150420042',
	            'text_alerts_ok': 'true',
	            'zipcode': '79900',
	            'description': 'Test user'
                    })
        vol = model.DBSession.query(model.User).filter_by(user_name='testPerson').first()
        ok_(vol is not None,"Failed to create the test user")

        # Created by a coordinator, so should start activated.
        perms = [p.permission_name for p in vol.permissions]
        ok_('respond_to_need' in perms,perms)
        vol_id = vol.user_id

        resp = self.app.get('/deactivate_volunteer?user_id={}'.format(vol_id),
                extra_environ=env, status=302)

        vol = model.DBSession.query(model.User).filter_by(user_name='testPerson').first()
        perms = [p.permission_name for p in vol.permissions]
        ok_('respond_to_need' not in perms,perms)

    def test_11_langsInForm(self):
        ''' Language proficiencies in volunteer info form. '''
        resp = self.app.get('/add_volunteer_start',status=200)
        ok_('lang_english' in resp.text,resp.text)
        ok_('lang_spanish' in resp.text,resp.text)

    def test_12_canEditLangs(self):
        ''' Language proficiencies can be edited. '''
        resp = self.app.post('/add_volunteer_post',status=302,
                params={
                    'user_name': 'testPerson',
	            'display_name': 'Test Person',
	            'pwd': 'testPwd',
	            'pwd2': 'testPwd',
	            'email': 'test@test.com',
	            'phone': '9150420042',
	            'text_alerts_ok': 'true',
	            'zipcode': '79900',
	            'description': 'Test user',
                    'lang_english': 'true',
                    'lang_spanish': 'false'
                    })
        vol = model.DBSession.query(model.User).filter_by(user_name='testPerson').first()
        ok_(vol is not None,"Failed to create the test user")
        eq_(1,vol.lang_english,"New volunteer should have English set. English {}, Spanish {}".\
                format(vol.lang_english,vol.lang_spanish))
        eq_(0,vol.lang_spanish,"New volunteer should not have Spanish set. English {}, Spanish {}".\
                format(vol.lang_english,vol.lang_spanish))

        env = {'REMOTE_USER':'testPerson'}
        resp = self.app.post('/add_volunteer_post',
                status=302,
                extra_environ=env,
                params={
                    'user_name': 'testPerson',
                    'display_name': 'Test Person',
                    'pwd': 'testPwd',
                    'pwd2': 'testPwd',
                    'email': 'test@test.com',
                    'phone': '9150420042',
                    'text_alerts_ok': 'true',
                    'zipcode': '79900',
                    'description': 'Test user',
                    'lang_english': 'false',
                    'lang_spanish': 'true'
                    })
        logging.getLogger('unter.test').error('Response: status={}, text=\n{}'.\
                format(resp.status,resp.text))
        vol = model.DBSession.query(model.User).filter_by(user_name='testPerson').first()
        ok_(vol is not None,"Failed to create the test user")
        eq_(0,vol.lang_english,"Edited volunteer should not have English set. English {}, Spanish {}".\
                format(vol.lang_english,vol.lang_spanish))
        eq_(1,vol.lang_spanish,"Edited volunteer should have Spanish set. English {}, Spanish {}".\
                format(vol.lang_english,vol.lang_spanish))


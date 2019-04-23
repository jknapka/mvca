'''
Test that password resets work.
'''
import sqlalchemy as sql
import sqlalchemy.orm as orm
import transaction
import traceback
import datetime as dt
import re
import time

import unter.model as model
import unter.controllers.need as need
import unter.controllers.alerts as alerts

from tg import expose, flash, require, url, lurl

from unter.tests import TestController

from nose.tools import ok_, eq_

from bs4 import BeautifulSoup as bsoup

from io import StringIO

import logging
import re

import unter.model as model
import unter.controllers.alerts as alerts
import unter.controllers.need as need

class TestPasswordResets(TestController):

    def setUp(self):
        super().setUp()

        self.createVolunteers()
        transaction.commit()

        alerts.EMAIL_ENABLED = True
        alerts.MIN_PWD_RESET_INTERVAL = None
        alerts.MAX_PWD_RESET_INTERVAL = 3600

    def test_0_passwordReset(self):
        ''' Check the complete password reset chain. '''
        v = self.getUser(model.DBSession,'veronica')
        v_pwd = v.password # This is just a hash, but we need to compare it later.
        email = v.email_address

        # We must be able to get the reset start page.
        resp = self.app.get('/forgot_pwd',status=200)
        ok_("Enter your email address to receive a password reset link" in resp.text,resp.text)
        zup = bsoup(resp.text,features="html.parser")
        inps = zup.find_all('input')
        eq_(inps[0].get('name'),'email_addr','No email_addr input field in response.')

        # We should be able to POST the form URL and
        # receive a password-reset email.
        resp = self.app.post('/forgot_pwd_post',status=200,
                params={'email_addr':email})
        ok_('If you entered a known email address, you will receive a password reset link' in resp.text,
                resp.text)

        # There should be one reset UUID, for Veronica.
        ruuids = model.DBSession.query(model.PasswordUUID).all()
        eq_(len(ruuids),1,"Got {} password UUIDs, expected 1".format(len(ruuids)))
        uid = ruuids[0].uuid
        logging.getLogger('unter.test').debug('Got reset UUID {} for user {}'.\
                format(uid,ruuids[0].user_id))

        # The reset link should exist in the email log.
        emailText = self.getEmailLog()
        linkRe = '({}(/reset_pwd\\?uuid={}&user_id={}))'.format(alerts.MVCA_SITE,uid,v.user_id)
        m = re.search(linkRe,emailText)
        logging.getLogger('unter.test').info('emailText is {}, m is {}\nlinkRe is {}'.format(emailText,m,linkRe))

        # If we get that link, we should get a form
        # with two password fields and a hidden UUID field.
        resetLink = m.groups()[1]
        logging.getLogger('unter.test').debug('Trying to get URL: {}'.format(resetLink))
        resp = self.app.get(resetLink,status=200)
        zup = bsoup(resp.text,features="html.parser")
        inps = zup.find_all('input')
        inpNames = [inp.get('name') for inp in inps]
        logging.getLogger('unter.test').debug('input names: {}'.format(inpNames))
        ok_('pwd' in inpNames,resp.text)
        ok_('pwd2' in inpNames,resp.text)
        ok_('uuid' in inpNames,resp.text)
        form = zup.find_all('form')
        eq_('/reset_pwd_post',form[0].get('action'),form[0])

        # If we POST the password reset form, we should be
        # able to change Veronica's password.
        resp = self.app.post('/reset_pwd_post',status=302,
                params={'pwd':'newPWD','pwd2':'newPWD','uuid':uid})

        v = self.getUser(model.DBSession,'veronica')
        ok_(v.password != v_pwd,"Veronica's password did not change!")

        # And the response should be the "Login" page.
        ok_("/login" in resp,resp)

    def test_1_passwordResetWithNoUUIDFails(self):
        ''' Check that a reset attempt with no matching UUID fails.'''
        v = self.getUser(model.DBSession,'veronica')
        v_pwd = v.password # This is just a hash, but we need to compare it later.
        email = v.email_address

        # We must be able to get the reset start page.
        resp = self.app.get('/forgot_pwd',status=200)
        ok_("Enter your email address to receive a password reset link" in resp.text,resp.text)
        zup = bsoup(resp.text,features="html.parser")
        inps = zup.find_all('input')
        eq_(inps[0].get('name'),'email_addr','No email_addr input field in response.')

        # We should be able to POST the form URL and
        # receive a password-reset email.
        resp = self.app.post('/forgot_pwd_post',status=200,
                params={'email_addr':email})
        ok_('If you entered a known email address, you will receive a password reset link' in resp.text,
                resp.text)

        # There should be one reset UUID, for Veronica.
        ruuids = model.DBSession.query(model.PasswordUUID).all()
        eq_(len(ruuids),1,"Got {} password UUIDs, expected 1".format(len(ruuids)))
        uid = ruuids[0].uuid
        logging.getLogger('unter.test').debug('Got reset UUID {} for user {}'.\
                format(uid,ruuids[0].user_id))
        #... but let's delete that.
        model.DBSession.delete(ruuids[0])
        transaction.commit()

        # The reset link should exist in the email log.
        emailText = self.getEmailLog()
        linkRe = '({}(/reset_pwd\\?uuid={}&user_id={}))'.format(alerts.MVCA_SITE,uid,v.user_id)
        m = re.search(linkRe,emailText)
        logging.getLogger('unter.test').info('emailText is {}, m is {}\nlinkRe is {}'.format(emailText,m,linkRe))

        # If we get that link, we should get a denial, claiming
        # we are not authorized to change the password.
        resetLink = m.groups()[1]
        logging.getLogger('unter.test').debug('Trying to get URL: {}'.format(resetLink))
        resp = self.app.get(resetLink,status=200)
        ok_('not authorized' in resp.text,resp.text)

    def test_2_passwordResetWithWrongUserFails(self):
        ''' Check that a reset attempt with an incorrect user ID fails.'''
        v = self.getUser(model.DBSession,'veronica')
        v_pwd = v.password # This is just a hash, but we need to compare it later.
        email = v.email_address

        # We must be able to get the reset start page.
        resp = self.app.get('/forgot_pwd',status=200)
        ok_("Enter your email address to receive a password reset link" in resp.text,resp.text)
        zup = bsoup(resp.text,features="html.parser")
        inps = zup.find_all('input')
        eq_(inps[0].get('name'),'email_addr','No email_addr input field in response.')

        # We should be able to POST the form URL and
        # receive a password-reset email.
        resp = self.app.post('/forgot_pwd_post',status=200,
                params={'email_addr':email})
        ok_('If you entered a known email address, you will receive a password reset link' in resp.text,
                resp.text)

        # There should be one reset UUID, for Veronica.
        ruuids = model.DBSession.query(model.PasswordUUID).all()
        eq_(len(ruuids),1,"Got {} password UUIDs, expected 1".format(len(ruuids)))
        uid = ruuids[0].uuid
        logging.getLogger('unter.test').debug('Got reset UUID {} for user {}'.\
                format(uid,ruuids[0].user_id))
        #... but let's change the user ID.
        ruuids[0].user_id = 1 # Manager.
        transaction.commit()

        # The reset link should exist in the email log.
        emailText = self.getEmailLog()
        linkRe = '({}(/reset_pwd\\?uuid={}&user_id={}))'.format(alerts.MVCA_SITE,uid,v.user_id)
        m = re.search(linkRe,emailText)
        logging.getLogger('unter.test').info('emailText is {}, m is {}\nlinkRe is {}'.format(emailText,m,linkRe))

        # If we get that link, we should get a denial, claiming
        # we are not authorized to change the password.
        resetLink = m.groups()[1]
        logging.getLogger('unter.test').debug('Trying to get URL: {}'.format(resetLink))
        resp = self.app.get(resetLink,status=200)
        ok_('not authorized' in resp.text,resp.text)

    def test_3_passwordResetTooEarlyFails(self):
        ''' Check that a reset attempt before the min reset interval elapses fails.'''
        v = self.getUser(model.DBSession,'veronica')
        v_pwd = v.password # This is just a hash, but we need to compare it later.
        email = v.email_address

        # Enforce that password reset links cannot be used until
        # two seconds elapse from their creation time.
        alerts.MIN_PWD_RESET_INTERVAL = 1
        alerts.MAX_PWD_RESET_INTERVAL = 3600

        # We must be able to get the reset start page.
        resp = self.app.get('/forgot_pwd',status=200)
        ok_("Enter your email address to receive a password reset link" in resp.text,resp.text)
        zup = bsoup(resp.text,features="html.parser")
        inps = zup.find_all('input')
        eq_(inps[0].get('name'),'email_addr','No email_addr input field in response.')

        # We should be able to POST the form URL and
        # receive a password-reset email.
        resp = self.app.post('/forgot_pwd_post',status=200,
                params={'email_addr':email})
        ok_('If you entered a known email address, you will receive a password reset link' in resp.text,
                resp.text)

        # There should be one reset UUID, for Veronica.
        ruuids = model.DBSession.query(model.PasswordUUID).all()
        eq_(len(ruuids),1,"Got {} password UUIDs, expected 1".format(len(ruuids)))
        uid = ruuids[0].uuid
        logging.getLogger('unter.test').debug('Got reset UUID {} for user {}'.\
                format(uid,ruuids[0].user_id))

        # The reset link should exist in the email log.
        emailText = self.getEmailLog()
        linkRe = '({}(/reset_pwd\\?uuid={}&user_id={}))'.format(alerts.MVCA_SITE,uid,v.user_id)
        m = re.search(linkRe,emailText)
        logging.getLogger('unter.test').info('emailText is {}, m is {}\nlinkRe is {}'.format(emailText,m,linkRe))

        # If we get that link, we should get a denial, claiming
        # the link cannot be used for one minute.
        resetLink = m.groups()[1]
        logging.getLogger('unter.test').debug('Trying to get URL: {}'.format(resetLink))
        resp = self.app.get(resetLink,status=200)
        ok_('too new' in resp.text,resp.text)

        # If we sleep for more than a second, though, it should work.
        time.sleep(1.2)

        resetLink = m.groups()[1]
        logging.getLogger('unter.test').debug('Trying to get URL: {}'.format(resetLink))
        resp = self.app.get(resetLink,status=200)
        zup = bsoup(resp.text,features="html.parser")
        inps = zup.find_all('input')
        inpNames = [inp.get('name') for inp in inps]
        logging.getLogger('unter.test').debug('input names: {}'.format(inpNames))
        ok_('pwd' in inpNames,resp.text)
        ok_('pwd2' in inpNames,resp.text)
        ok_('uuid' in inpNames,resp.text)
        form = zup.find_all('form')
        eq_('/reset_pwd_post',form[0].get('action'),form[0])

    def test_4_passwordResetTooLateFails(self):
        ''' Check that a reset attempt with an expired link fails.'''
        v = self.getUser(model.DBSession,'veronica')
        v_pwd = v.password # This is just a hash, but we need to compare it later.
        email = v.email_address

        # Enforce that password reset links cannot be used AFTER
        # two seconds elapse from their creation time.
        alerts.MAX_PWD_RESET_INTERVAL = 1
        alerts.MIN_PWD_RESET_INTERVAL = None

        # We must be able to get the reset start page.
        resp = self.app.get('/forgot_pwd',status=200)
        ok_("Enter your email address to receive a password reset link" in resp.text,resp.text)
        zup = bsoup(resp.text,features="html.parser")
        inps = zup.find_all('input')
        eq_(inps[0].get('name'),'email_addr','No email_addr input field in response.')

        # We should be able to POST the form URL and
        # receive a password-reset email.
        resp = self.app.post('/forgot_pwd_post',status=200,
                params={'email_addr':email})
        ok_('If you entered a known email address, you will receive a password reset link' in resp.text,
                resp.text)

        # There should be one reset UUID, for Veronica.
        ruuids = model.DBSession.query(model.PasswordUUID).all()
        eq_(len(ruuids),1,"Got {} password UUIDs, expected 1".format(len(ruuids)))
        uid = ruuids[0].uuid
        logging.getLogger('unter.test').debug('Got reset UUID {} for user {}'.\
                format(uid,ruuids[0].user_id))

        # The reset link should exist in the email log.
        emailText = self.getEmailLog()
        linkRe = '({}(/reset_pwd\\?uuid={}&user_id={}))'.format(alerts.MVCA_SITE,uid,v.user_id)
        m = re.search(linkRe,emailText)
        logging.getLogger('unter.test').info('emailText is {}, m is {}\nlinkRe is {}'.format(emailText,m,linkRe))

        # If we sleep for more than one second, the reset link should fail.
        time.sleep(1.2)
        resetLink = m.groups()[1]
        logging.getLogger('unter.test').debug('Trying to get URL: {}'.format(resetLink))
        resp = self.app.get(resetLink,status=200)
        ok_('has expired' in resp.text,resp.text)

    def test_5_passwordResetLinksUsableOnceOnly(self):
        ''' Check that password reset links are usable only once. '''
        v = self.getUser(model.DBSession,'veronica')
        v_pwd = v.password # This is just a hash, but we need to compare it later.
        email = v.email_address

        # We must be able to get the reset start page.
        resp = self.app.get('/forgot_pwd',status=200)
        ok_("Enter your email address to receive a password reset link" in resp.text,resp.text)
        zup = bsoup(resp.text,features="html.parser")
        inps = zup.find_all('input')
        eq_(inps[0].get('name'),'email_addr','No email_addr input field in response.')

        # We should be able to POST the form URL and
        # receive a password-reset email.
        resp = self.app.post('/forgot_pwd_post',status=200,
                params={'email_addr':email})
        ok_('If you entered a known email address, you will receive a password reset link' in resp.text,
                resp.text)

        # There should be one reset UUID, for Veronica.
        ruuids = model.DBSession.query(model.PasswordUUID).all()
        eq_(len(ruuids),1,"Got {} password UUIDs, expected 1".format(len(ruuids)))
        uid = ruuids[0].uuid
        logging.getLogger('unter.test').debug('Got reset UUID {} for user {}'.\
                format(uid,ruuids[0].user_id))

        # The reset link should exist in the email log.
        emailText = self.getEmailLog()
        linkRe = '({}(/reset_pwd\\?uuid={}&user_id={}))'.format(alerts.MVCA_SITE,uid,v.user_id)
        m = re.search(linkRe,emailText)
        logging.getLogger('unter.test').info('emailText is {}, m is {}\nlinkRe is {}'.format(emailText,m,linkRe))

        # If we get that link, we should get a form
        # with two password fields and a hidden UUID field.
        resetLink = m.groups()[1]
        logging.getLogger('unter.test').debug('Trying to get URL: {}'.format(resetLink))
        resp = self.app.get(resetLink,status=200)
        zup = bsoup(resp.text,features="html.parser")
        inps = zup.find_all('input')
        inpNames = [inp.get('name') for inp in inps]
        logging.getLogger('unter.test').debug('input names: {}'.format(inpNames))
        ok_('pwd' in inpNames,resp.text)
        ok_('pwd2' in inpNames,resp.text)
        ok_('uuid' in inpNames,resp.text)
        form = zup.find_all('form')
        eq_('/reset_pwd_post',form[0].get('action'),form[0])

        # If we POST the password reset form, we should be
        # able to change Veronica's password.
        resp = self.app.post('/reset_pwd_post',status=302,
                params={'pwd':'newPWD','pwd2':'newPWD','uuid':uid})

        v = self.getUser(model.DBSession,'veronica')
        ok_(v.password != v_pwd,"Veronica's password did not change!")

        # And the response should be the "Login" page.
        ok_("/login" in resp,resp)

        # If we try to get the reset link again, we should
        # get a "not authorized" message.
        resp = self.app.get(resetLink,status=200)
        ok_("not authorized" in resp.text,resp.text)

        # If we try to post the reset form again, we should
        # get a "not authorized" message.
        resp = self.app.post('/reset_pwd_post',status=200,
                params={'pwd':'newPWD','pwd2':'newPWD','uuid':uid})
        ok_("not authorized" in resp.text,resp.text)

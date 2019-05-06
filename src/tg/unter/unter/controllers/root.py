# -*- coding: utf-8 -*-
"""Main Controller"""

import time
import datetime
import logging
import uuid
import re

from tg import expose, flash, require, url, lurl
from tg import request, redirect, tmpl_context
from tg.i18n import ugettext as _, lazy_ugettext as l_
from tg.exceptions import HTTPFound
from tg import predicates
from tg import config
from unter import model
from unter.controllers.secure import SecureController
from unter.model import DBSession
from tgext.admin.tgadminconfig import BootstrapTGAdminConfig as TGAdminConfig
from tgext.admin.controller import AdminController

from unter.lib.base import BaseController
from unter.controllers.error import ErrorController
from unter.controllers.need import checkOneEvent, checkValidEvents

from unter.controllers.forms import NewAcctForm,AvailabilityForm,NeedEventForm,AddEventTypeForm

from unter.controllers.util import *
import unter.controllers.need as need
import unter.controllers.alerts as alerts
import unter.controllers.util as util

from sqlalchemy import or_,text

__all__ = ['RootController']

def getLogger():
    return logging.getLogger('unter.root')

class RootController(BaseController):
    """
    The root controller for the unter application.

    All the other controllers and WSGI applications should be mounted on this
    controller. For example::

        panel = ControlPanelController()
        another_app = AnotherWSGIApplication()

    Keep in mind that WSGI applications shouldn't be mounted directly: They
    must be wrapped around with :class:`tg.controllers.WSGIAppController`.

    """
    secc = SecureController()
    admin = AdminController(model, DBSession, config_type=TGAdminConfig)

    error = ErrorController()

    def _before(self, *args, **kw):
        tmpl_context.project_name = config.get("mvca.site.name","MVCA")


    #==================================
    # Volunteer management.
    #==================================

    @expose('unter.templates.add_volunteer_start')
    def add_volunteer_start(self,form=None,error_msg=None,user_id=None):
        ''' Show the "Add a volunteer" page. '''
        editing = False
        user = None
        loggedInUser = None
        if user_id is not None:
            user_id = int(user_id)
        if user_id is not None and request.identity:
            # We want to edit an existing volunteer.
            loggedInUser= self.getVolunteerIdentity()
            user = model.DBSession.query(model.User).filter_by(user_id=user_id).first()
            if user is not None:
                if (user.user_id != loggedInUser.user_id) and not util.isUserManager(loggedInUser):
                    flash(_("You may only edit your own volunteer information."))
                    redirect('/volunteer_info')
                form = self.getExistingVolunteerForm(user)
                editing = True
        if form is None:
            form = NewAcctForm()
        return dict(page='add_volunteer_start',form=form,url='/add_volunteer_post',
                error_msg=error_msg,editing=editing,user=user,requesting_user=loggedInUser)

    def getExistingVolunteerForm(self,user):
        ''' Populate a NewAcctForm with the data for user. '''
        if user is None:
            return None
        form = NewAcctForm()
        form.user_name.data = user.user_name
        form.display_name.data = user.display_name
        form.pwd.data = ''
        form.pwd2.data = ''
        form.email.data = user.email_address
        form.phone.data = user.phone
        form.text_alerts_ok.data = user.text_alerts_ok == 1
        form.zipcode.data = user.zipcode
        form.description.data = user.description
        form.lang_english.data = user.lang_english == 1
        form.lang_spanish.data = user.lang_spanish == 1
        return form

    @expose('unter.templates.add_volunteer_start')
    def add_volunteer_post(self,**kwargs):
        ''' Try to create a new volunteer. '''
        form = NewAcctForm(request.POST)
        if not form.validate():
            getLogger().info('Form failed to validate: {}'.\
                    format(form.errors))
            return self.add_volunteer_start(form=form)
        else:
            thing = Thing()
            form.populate_obj(thing)
            thing.phone = ''.join(re.split('[^0-9]',thing.phone))
            thing.print()

            user_name = thing.user_name
            email = thing.email
            pwd = thing.pwd
            pwd2 = thing.pwd2

            existingUser = model.User.by_user_name(user_name)
            if existingUser is not None:
                if not request.identity:
                    # It's not OK to try to establish a new account
                    # with the same user name as an existing one.
                    getLogger().info('Refusing to add second user named {}'.format(user_name))
                    return self.add_volunteer_start(form=form,error_msg='Account %s already exists'%user_name)
                user = self.getVolunteerIdentity()
                if user.user_name == thing.user_name:
                    # It's OK for users to edit their own data.
                    getLogger().info('Editing self with user name {}'.format(user_name))
                    self.edit_volunteer(existingUser,thing)
                if predicates.has_permission('manage_events') or predicates.has_permission('manage'):
                    # It's OK for coordinators to edit other volunteers' data.
                    getLogger().info('Editing {} with user name {}'.\
                            format(request.identity['repoze.who.userid'],user_name))
                    self.edit_volunteer(existingUser,thing)
            existingUser = model.User.by_email_address(email)
            if existingUser is not None:
                return self.add_volunteer_start(form=form,error_msg='Email address %s is in use, please use a different one'%email)

            if len(pwd) == 0:
                return self.add_volunteer_start(form=form,error_msg='You must provide a password.')

            acct = model.User(user_name=user_name, email_address=email,display_name=thing.display_name,
                    description=thing.description,
                    phone=thing.phone,
                    text_alerts_ok={True:1,False:0}[thing.text_alerts_ok],
                    zipcode=thing.zipcode,
                    lang_english={True:1,False:0}[thing.lang_english],
                    lang_spanish={True:1,False:0}[thing.lang_spanish])
            acct.password = pwd
            DBSession.add(acct)
            acct = model.User.by_email_address(email)

            # before they can respond to events.
            # Add the volunteer to the 'volunteers' group. To promote a
            # volunteer to a coordinator, add them to the 'coordinators' group
            # via the admin interface (/admin/ URL - you must be logged in as
            # 'manager' to use that).
            # EXCEPT: only do this if the logged-in user is a coordinator
            # or manager.
            user = self.getVolunteerIdentity()
            if user is not None:
                if util.isUserManager(user):
                    volGroup = DBSession.query(model.Group).filter_by(group_name='volunteers').first()
                    volGroup.users.append(acct)

            if not request.identity:
                flash("Please log in and let us know when you are available.")
                redirect(lurl('/login'))
            else:
                flash("Volunteer {} added".format(user_name))
                user = self.getVolunteerIdentity()
                if 'manage_events' in [p.permission_name for p in user.permissions]:
                    page = '/coord_page'
                else:
                    # Hmm, we might not want to allow this :-/
                    page = '/volunteer_info'
                redirect(lurl(page,dict(message="Volunteer {} added".format(user_name))))

    def edit_volunteer(self,user,attribs):
        '''
        Called when posting a new-account form for an existing user,
        if that is allowed for the logged-in user. This allows users
        to edit their own info, and coordinators to edit anyone's info.
        '''
        user.email_address = attribs.email
        user.display_name = attribs.display_name
        if len(attribs.pwd) > 0:
            user.password = attribs.pwd
        user.description = attribs.description
        user.phone = attribs.phone
        user.zipcode = attribs.zipcode
        user.text_alerts_ok = {True:1,False:0,1:1,0:0}[attribs.text_alerts_ok]
        user.lang_english = {True:1,False:0,1:1,0:0}[attribs.lang_english]
        user.lang_spanish = {True:1,False:0,1:1,0:0}[attribs.lang_spanish]
        redirect(lurl("/volunteer_info"),dict(user_id=user.user_id))

    @expose()
    @require(predicates.Any(\
            predicates.has_permission('manage_events'),\
            predicates.has_permission('manage')))
    def deactivate_volunteer(self,user_id):
        u = model.DBSession.query(model.User).filter_by(user_id=user_id).first()
        if u is not None:
            g = model.DBSession.query(model.Group).filter_by(group_name='volunteers').first()
            g.users.remove(u)
        redirect(lurl("/volunteer_info"),dict(user_id=user_id))

    @expose()
    @require(predicates.Any(\
            predicates.has_permission('manage_events'),\
            predicates.has_permission('manage')))
    def activate_volunteer(self,user_id):
        u = model.DBSession.query(model.User).filter_by(user_id=user_id).first()
        if u is not None:
            g = model.DBSession.query(model.Group).filter_by(group_name='volunteers').first()
            g.users.append(u)
        redirect(lurl("/volunteer_info"),dict(user_id=user_id))

    @expose()
    @require(predicates.has_permission('manage'))
    def promote_to_coordinator(self,user_id):
        self.promote(user_id,'coordinators')

    @expose()
    @require(predicates.has_permission('manage'))
    def promote_to_manager(self,user_id):
        self.promote(user_id,'managers')

    @expose()
    @require(predicates.has_permission('manage'))
    def unpromote(self,user_id):
        log = getLogger()
        log.info("Trying to un-promote {}".format(user_id))
        if user_id is not None:
            user_id = int(user_id)
        u = model.DBSession.query(model.User).filter_by(user_id=user_id).first()
        if u is not None:
            for g in u.groups:
                if g.group_name == 'managers':
                    try:
                        g.users.remove(u)
                        log.info("  Removed user from managers group.")
                    except ValueError:
                        pass
                if g.group_name == 'coordinators':
                    try:
                        g.users.remove(u)
                        log.info("  Removed user from coordinators group.")
                    except ValueError:
                        pass
        redirect(lurl("/volunteer_info"),dict(user_id=user_id))

    def promote(self,user_id,groupName):
        user_id = int(user_id)
        log = getLogger()
        log.info("Trying to promote {} to group {}".format(user_id,groupName))
        u = model.DBSession.query(model.User).filter_by(user_id=user_id).first()
        if u is not None:
            group = model.DBSession.query(model.Group).filter_by(group_name=groupName).first()
            if group is not None:
                group.users.append(u)
                log.info('  Promoted {} to {}.'.format(u.user_name,groupName))
                redirect(lurl('/volunteer_info'),dict(user_id=user_id))
            else:
                log.error("  Could not promote to non-existing group {}".format(groupName))
                redirect(lurl('/volunteer_info'),dict(user_id=user_id))
        else:
            log.error("  Could not promote non-existing user_id {}".format(user_id))
            redirect(lurl('/volunteer_info'))

    @expose('unter.templates.add_availability_start')
    @require(predicates.not_anonymous())
    def add_availability_start(self,form=None):
        ''' Present the "add a time slot" form. '''
        user = self.getVolunteerIdentity()
        user_id = user.user_id
        if form is None:
            form = AvailabilityForm(user_id=user_id)
        return dict(page='add_availability_start',form=form,url='/add_availability_post')

    @expose('unter.templates.add_availability_start')
    @require(predicates.not_anonymous())
    def add_availability_post(self,**kwargs):
        form = AvailabilityForm(request.POST)
        if not form.validate:
            return self.add_availability_start(user_id=form.user_id.data,form=form)
        else:
            print("Availability form data is valid.")
            tfdict = {True:1,False:0}
            obj = Thing()
            form.populate_obj(obj)
            obj.print("Availability:")

            avail = model.VolunteerAvailability(user_id=int(obj.user_id),
                    dow_sunday = tfdict[obj.dow_sunday],
                    dow_monday = tfdict[obj.dow_monday],
                    dow_tuesday = tfdict[obj.dow_tuesday],
                    dow_wednesday = tfdict[obj.dow_wednesday],
                    dow_thursday = tfdict[obj.dow_thursday],
                    dow_friday = tfdict[obj.dow_friday],
                    dow_saturday = tfdict[obj.dow_saturday],
                    start_time = minutesPastMidnight(obj.start_time),
                    end_time = minutesPastMidnight(obj.end_time))
            DBSession.add(avail)

            redirect(lurl('/volunteer_info'))

    @expose('unter.templates.volunteer_info')
    @require(predicates.not_anonymous())
    def volunteer_info(self,user_id=None,**kwargs):
        '''
        Show the info page for a given volunteer, or (if no user_id
        is specified) for the logged-in user. Only managers and
        coordinators can view other users' info.
        '''
        if user_id is not None:
            user_id = int(user_id)
        if not request.identity:
            login_counter = request.environ.get('repoze.who.logins', 0) + 1
            redirect('/login',
                     params=dict(came_from="/volunteer_info",__logins=login_counter))

        # The logged-in user is the "requesting" user.
        user = self.getVolunteerIdentity()
        requesting_user = user
        if user_id is not None and user_id != user.user_id:
            # Only managers and coordinators can view other users' info.
            if predicates.has_permission('manage_events') or predicates.has_permission('manage'):
                user = self.getVolunteerIdentity(userId=user_id)
            else:
                flash("You may only view your own volunteer page.")
                redirect("/volunteer_info")

        # At this point, we know the requesting_user is
        # either requesting their own data, or allowed to
        # view the user's data.
        availabilities = [self.toRawAvailability(av) for av in user.volunteer_availability]
        events_responded = [vr.need_event for vr in user.volunteer_response if vr.need_event.complete == 0]
        events_responded = [toWrappedEvent(ev) for ev in events_responded]
        events_available = need.getAvailableEventsForVolunteer(model.DBSession,user)
        events_available = [toWrappedEvent(ev) for ev in events_available]

        return dict(user=user,
                requesting_user=requesting_user,
                availabilities=availabilities,
                events=events_responded,
                events_available=events_available,
                message='')

    @expose('unter.templates.all_volunteers')
    @require(predicates.has_permission('manage_events'))
    def all_volunteers(self):
        users = model.DBSession.query(model.User).all()
        user = self.getVolunteerIdentity()
        return dict(all_volunteers=users,user=user)

    @expose()
    @require(predicates.not_anonymous())
    def remove_availability(self,vaid,came_from=lurl('/volunteer_info')):
        av = model.DBSession.query(model.VolunteerAvailability).filter_by(vaid=vaid).first()
        if av is not None:
            user = self.getVolunteerIdentity()
            if av.user.user_id == user.user_id or util.isUserManager(user):
                model.DBSession.delete(av)
                flash("Available time removed.")
            else:
                flash('You may only manager your own available times.')
        else:
            flash("No such available time found.")
        redirect(came_from)

    @expose()
    @require(predicates.not_anonymous())
    def decommit(self,neid,came_from=lurl('/volunteer_info')):
        user = self.getVolunteerIdentity()
        vr = model.DBSession.query(model.VolunteerResponse).filter_by(neid=neid).filter_by(user_id=user.user_id).first()
        if vr is not None:
            need.decommit_volunteer(model.DBSession,vcom=vr)
            flash("Commitment cancelled. Thanks for letting us know!")
        else:
            #flash("No such commitment found for {}.".format(user.display_name))
            ev = model.DBSession.query(model.NeedEvent).filter_by(neid=neid).first()
            if ev is not None:
                flash('OK, we won\'t bother you about that event again.')
                need.decommit_volunteer(model.DBSession,user=user,ev=ev)
            else:
                pass
        redirect(came_from)

    def toRawAvailability(self,av):
        ''' Convert a model VolunteerAvailability object to a plain ol' Python
        object containing the same data in a format easy for templates to
        digest. '''
        result = Thing()
        result.dow_sunday = av.dow_sunday
        result.dow_monday = av.dow_monday
        result.dow_tuesday = av.dow_tuesday
        result.dow_wednesday = av.dow_wednesday
        result.dow_thursday = av.dow_thursday
        result.dow_friday = av.dow_friday
        result.dow_saturday = av.dow_saturday
        result.start_time = minutesPastMidnightToTimeString(av.start_time)
        result.end_time = minutesPastMidnightToTimeString(av.end_time)
        result.av = av
        return result

    #==================================
    # Password reset handling.
    #==================================
    @expose('unter.templates.forgot_pwd')
    def forgot_pwd(self):
        if request.identity:
            redirect('/',status=403)
        return dict()

    @expose()
    def forgot_pwd_post(self,email_addr):
        foundExistingPuuid = False
        u = model.User.by_email_address(email_addr)
        resultMsg = "If you entered a known email address, you will receive a"+\
            " password reset link message at that address. Search for 'MVCA' in your inbox."
        if u is not None:
            existingPuuids = model.DBSession.query(model.PasswordUUID).filter_by(user_id=u.user_id).all()
            if len(existingPuuids) > 0:
                now = time.time()
                for exPuuid in existingPuuids:
                    if alerts.MAX_PWD_RESET_INTERVAL is not None and \
                        now - alerts.MAX_PWD_RESET_INTERVAL > exPuuid.create_time:
                            # This one is expired, delete it.
                            model.DBSession.delete(exPuuid)
                    else:
                        # There is at least one non-expired request, so we
                        # shouldn't send another.
                        foundExistingPuuid = True
                        mgr = model.DBSession.query(model.User).filter_by(user_name='manager').first()
                        mgrEmail = mgr.email_address
                        mgrPhone = mgr.phone
                        resultMsg = 'You have already requested a password reset link. If you '+\
                                'did not receive an email, contact the site manager at '+\
                                '{} or {} to reset your password.'.format(mgrEmail,mgrPhone)

        if u is not None and not foundExistingPuuid:
            # We send the reset link email only if the user exists and
            # has not recently requested a reset email.
            emailer = alerts.getEmailAlerter()
            uid = str(uuid.uuid4())
            puuid = model.PasswordUUID()
            puuid.user = u
            puuid.uuid = uid
            puuid.create_time = time.time()
            model.DBSession.add(puuid)
            model.DBSession.flush()
            link = lurl('{}/reset_pwd?uuid={}&user_id={}'.format(alerts.MVCA_SITE,uid,u.user_id))
            msg = "Someone, perhaps you, requested a reset of your"+\
                " Migrant Volunteer Coordination Assistant password."+\
                " If you did request a password reset, click the link"+\
                " in order to reset your password.<br/>{}".format(link)
            emailer(message=msg,toAddr=email_addr,subject="MVCA password reset request - do not reply")
        return resultMsg
    
    @expose('unter.templates.reset_pwd')
    def reset_pwd(self,uuid,user_id):
        now = time.time()
        ruuid = model.DBSession.query(model.PasswordUUID).filter_by(uuid=uuid).first()
        
        if ruuid is None or ruuid.user_id != int(user_id):
            getLogger().warn('Password reset attempted with invalid UUID {} for user ID {}'.format(uuid,user_id))
            return 'You are not authorized to reset this password.'
        if now - alerts.MAX_PWD_RESET_INTERVAL > ruuid.create_time:
            model.DBSession.delete(ruuid)
            return 'This reset link has expired. Visit <a href="/forgot_pwd">the reset page</a>'+\
                    'to request a new one.'
        if alerts.MIN_PWD_RESET_INTERVAL is not None:
            if now - alerts.MIN_PWD_RESET_INTERVAL < ruuid.create_time:
                return 'This reset link is too new. Please try again in one minute.'
        return dict(uuid=uuid)

    @expose()
    def reset_pwd_post(self,pwd,pwd2,uuid):
        now = time.time()
        ruuid = model.DBSession.query(model.PasswordUUID).filter_by(uuid=uuid).first()
        
        if ruuid is None:
            getLogger().warn('Password reset POST attempted with invalid UUID {}'.format(uuid))
            return 'You are not authorized to reset this password.'
        if now - alerts.MAX_PWD_RESET_INTERVAL > ruuid.create_time:
            return 'This reset link has expired. Visit <a href="/forgot_pwd">the reset page</a>'+\
                    'to request a new one.'
        if alerts.MIN_PWD_RESET_INTERVAL is not None:
            if now - alerts.MIN_PWD_RESET_INTERVAL < ruuid.create_time:
                return 'This reset link is too new. Please try again in one minute.'

        if pwd != pwd2:
            flash("The passwords to not match.")
            redirect("/forgot_pwd")
        u = model.DBSession.query(model.User).filter_by(user_id=ruuid.user_id).first()
        if u is None:
            getLogger().warn('Password reset POST attempted with nonexistent user {}'.format(ruuid.user_id))
            return 'You are not authorized to reset this password.'

        # Looks like everything is OK, we can actually
        # change the password now. First we must delete
        # the UUID row so that the link cannot be used
        # again.
        model.DBSession.delete(ruuid)
        u.password = pwd
        flash('Your password has been changed.')
        redirect('/login')
        

    #==================================
    # Coordinator pages.
    #==================================

    @expose('unter.templates.coord_page')
    @require(predicates.has_permission('manage_events'))
    def coord_page(self,**kwargs):
        user = self.getVolunteerIdentity()
        if user is None:
            redirect(lurl('/login'))
        events = model.DBSession.query(model.NeedEvent).filter_by(created_by=user).all()
        events = [toWrappedEvent(ev) for ev in events if ev.complete == 0]
        return dict(user=user,events=events,message='')

    def getVolunteerIdentity(self,userId=None):
        user = None
        if userId is None:
            ''' Get the logged-in user's volunteer identity. '''
            if request.identity is not None and 'repoze.who.userid' in request.identity:
                userid = request.identity['repoze.who.userid']
                user = model.User.by_user_name(userid)
        else:
            ''' Get the identity for the given user. '''
            userId = int(userId)
            user = model.DBSession.query(model.User).filter_by(user_id=userId).first()
        return user

    #==================================
    # Need event management.
    #==================================

    @expose()
    def respond(self,neid):
        '''
        Called when a user clicks a response link on the web page.
        '''
        user = self.getVolunteerIdentity()
        getLogger().info('Responding to event {} on behalf of {}'.\
                format(neid,user))
        if user is None:
            redirect(lurl('/login'))
        nev = model.DBSession.query(model.NeedEvent).filter_by(neid=neid).first()
        if nev is not None:
            need.commit_volunteer(model.DBSession,user,nev)
        else:
            getLogger().warn('Cannot respond to nonexisting event {}'.\
                    format(nev.neid))
        redirect(lurl('/volunteer_info',dict(user_id=user.user_id,message='')))

    @expose()
    def sms_response(self,uuid,action):
        '''
        Called when a volunteer clicks a response link in an SMS message.
        The UUID points to an AlertUUID row giving us the user and event,
        and the action is either "accept" or "refuse".
        '''
        user,nev = alerts.getUserAndEventForUUID(uuid)
        if user is not None and nev is not None:
            if action == 'accept':
                getLogger().info("Accepting event {} for user {}.".format(nev.neid,user.user_id))
                need.commit_volunteer(model.DBSession,user=user,nev=nev)
                return "Thank you for responding. You will receive a reminder one hour prior to the event."
            if action == 'refuse':
                getLogger().info('Removing response for {} event {}.'.format(user.user_name,nev.neid))
                need.decommit_volunteer(model.DBSession,user=user,ev=nev)
        return 'Thank you for responding.'

    @expose('unter.templates.add_event_type_start')
    @require(predicates.has_permission('manage_events'))
    def add_event_type_start(self,form=None,**kwargs):
        ''' Present the "Add type of need" form. '''
        if form is None:
            form = AddEventTypeForm()
        return dict(page='add_event_type_start',form=form,url='/add_event_type_post')

    @expose('unter.templates.add_event_type_start')
    @require(predicates.has_permission('manage_events'))
    def add_event_type_post(self,name,description):
        ''' Process the "add event type" form. '''
        form = AddEventTypeForm(request.POST)
        if not form.validate():
            return dict(page='add_event_type_start',form=form,url='/add_event_type_post')
        et = model.EventType.et_by_name(name)
        if et is not None:
            flash('An event type named {} already exists.'.format(name))
            redirect('/add_need_event_start')
        et = model.EventType(name=name,description=description)
        model.DBSession.add(et)
        redirect('/add_need_event_start')

    @expose('unter.templates.add_need_event_start')
    @require(predicates.has_permission('manage_events'))
    def add_need_event_start(self,form=None,**kwargs):
        ''' Present the "add a need event" form. '''
        if form is None:
            form = NeedEventForm()
        user = self.getVolunteerIdentity()
        return dict(page='add_need_event_start',form=form,url='/add_need_event_post',user=user)

    @expose('unter.templates.add_need_event_start')
    @require(predicates.has_permission('manage_events'))
    def add_need_event_post(self,**kwargs):
        form = NeedEventForm(request.POST)
        if not form.validate():
            return self.add_need_event_start(form=form)
        else:
            obj = Thing()
            form.populate_obj(obj)
            obj.print("NeedEvent:")

            user = self.getVolunteerIdentity()

            dt = datetime.datetime(obj.date_of_need.year,
                    obj.date_of_need.month,
                    obj.date_of_need.day,
                    hour=12)

            nev = model.NeedEvent(etid=int(obj.ev_type),
                    duration=int(obj.duration),
                    date_of_need=int(dt.timestamp()),
                    time_of_need=minutesPastMidnight(obj.time_of_need),
                    volunteer_count=int(obj.volunteer_count),
                    affected_persons=int(obj.affected_persons),
                    notes=obj.notes,complete=0,location=obj.location,
                    created_by=user)
            DBSession.add(nev)
            DBSession.flush()

            self.check_need_events(ev_id=nev.neid)

            redirect(lurl('/need_events'))

    @expose('unter.templates.need_events')
    @require(predicates.not_anonymous())
    def need_events(self,completed=0,**kwargs):
        completed = int(completed)
        evs = DBSession.query(model.NeedEvent).filter(model.NeedEvent.complete == completed).all()
        now = datetime.date.today()
        evs = [toWrappedEvent(ev,now) for ev in evs]
        evs = [ev for ev in evs if ev.ev.complete==completed]
        evs.sort(key=lambda ev: (ev.ev.date_of_need,ev.ev.time_of_need),reverse=True)
        user = self.getVolunteerIdentity()
        isCoordinator = False
        if user is not None:
            print("user.permissions: {}".format(user.permissions))
            isCoordinator = 'manage_events' in [perm.permission_name for perm in user.permissions]
        return dict(user=user,isCoordinator=isCoordinator,evs=evs,complete=completed)

    @expose()
    @require(predicates.has_permission('manage_events'))
    def event_complete(self,neid):
        ''' Mark a need event as being complete. '''
        ev = DBSession.query(model.NeedEvent).filter(model.NeedEvent.neid == neid).first()
        if ev is not None:
            print("Got need event {}".format(neid))
            ev.complete = 1
        else:
            print("No such need event {}".format(neid))
        redirect(lurl("/need_events"))

    @expose()
    @require(predicates.has_permission('manage_events'))
    def cancel_event(self,neid):
        ev = DBSession.query(model.NeedEvent).filter_by(neid=neid).first()
        if ev is not None:
            getLogger().info('Cancelling event {}'.format(neid))
            need.cancelEvent(model.DBSession,ev,sendAlerts=True)
            flash('Event cancelled.')
        else:
            flash('Cannot find that event.')
        redirect(lurl('/need_events'))

    @expose('json')
    def check_need_events(self,ev_id=None):
        print("Checking events with ev_id={}".format(ev_id))

        if ev_id is not None:
            checkOneEvent(DBSession,ev_id)
        else:
            now = datetime.datetime.now()
            checkActiveEvents(DBSession,now)
        return dict()

    @expose('unter.templates.event_details')
    def event_details(self,neid):
        user = self.getVolunteerIdentity()
        nev = model.DBSession.query(model.NeedEvent).filter_by(neid=neid).first()
        vols = need.getAvailableVolunteers(model.DBSession,nev)
        vols = need.getUncommittedVolunteers(model.DBSession,nev,vols)
        committed = need.getCommittedVolunteers(model.DBSession,nev)
        now = datetime.date.today()
        nev = toWrappedEvent(nev,now)
        return dict(ev=nev,volunteers=vols,user=user,volunteers_committed=committed)

    #==================================
    # Alerts.
    #==================================

    @expose()
    @require(predicates.has_permission('manage_events'))
    def send_alert(self,neid,came_from=lurl('/coord_page')):
        ''' Send an alert for a specific event. '''
        need.checkOneEvent(model.DBSession,neid)
        redirect(came_from)

    @expose()
    @require(predicates.has_permission('manage_events'))
    def check_events(self,came_from=lurl('/need_events?complete=0')):
        '''
        Check all events for alert-ability and send alerts for
        any eligible ones.
        '''
        need.checkValidEvents(model.DBSession)
        redirect(came_from)

    #==================================
    # TG quickstart boilerplate follows.
    #==================================

    @expose('unter.templates.index')
    def index(self):
        """Handle the front-page."""
        return dict(page='index')

    @expose('unter.templates.about')
    def about(self):
        """Handle the 'about' page."""
        return dict(page='about')

    @expose('unter.templates.environ')
    def environ(self):
        """This method showcases TG's access to the wsgi environment."""
        return dict(page='environ', environment=request.environ)

    @expose('unter.templates.data')
    @expose('json')
    def data(self, **kw):
        """
        This method showcases how you can use the same controller
        for a data page and a display page.
        """
        return dict(page='data', params=kw)

    @expose('unter.templates.index')
    @require(predicates.has_permission('manage', msg=l_('Only for managers')))
    def manage_permission_only(self, **kw):
        """Illustrate how a page for managers only works."""
        return dict(page='managers stuff')

    @expose('unter.templates.index')
    @require(predicates.is_user('editor', msg=l_('Only for the editor')))
    def editor_user_only(self, **kw):
        """Illustrate how a page exclusive for the editor works."""
        return dict(page='editor stuff')

    @expose('unter.templates.login')
    def login(self, came_from=lurl('/'), failure=None, login='', message=''):
        """Start the user login."""
        if request.identity:
            redirect(lurl('/post_login'))
        if failure is not None:
            if failure == 'user-not-found':
                flash(_('User not found'), 'error')
            elif failure == 'invalid-password':
                flash(_('Invalid Password'), 'error')

        login_counter = request.environ.get('repoze.who.logins', 0)
        if failure is None and login_counter > 0:
            flash(_('Wrong credentials'), 'warning')

        return dict(page='login', login_counter=str(login_counter),
                    came_from=came_from, login=login, message=message)

    @expose()
    def post_login(self, came_from=lurl('/volunteer_info')):
        """
        Redirect the user to the initially requested page on successful
        authentication or redirect her back to the login page if login failed.

        """
        if not request.identity:
            login_counter = request.environ.get('repoze.who.logins', 0) + 1
            redirect('/login',
                     params=dict(came_from=came_from, __logins=login_counter))
        printDict(request.identity,"request.identity:")
        userid = request.identity['repoze.who.userid']
        flash(_('Welcome back, %s!') % userid)

        user = model.User.by_user_name(userid)

        # Do not use tg.redirect with tg.url as it will add the mountpoint
        # of the application twice.
        if predicates.in_group('volunteers'):
            came_from = lurl('/volunteer_info',params=dict(message=''))
        if predicates.in_group('coordinators'):
            came_from = lurl('/coord_page',params=dict(message=''))
        return HTTPFound(location=came_from)

    @expose()
    def post_logout(self, came_from=lurl('/')):
        """
        Redirect the user to the initially requested page on logout and say
        goodbye as well.

        """
        flash(_('We hope to see you soon!'))
        return HTTPFound(location=came_from)

# -*- coding: utf-8 -*-
"""Main Controller"""

import datetime

from tg import expose, flash, require, url, lurl
from tg import request, redirect, tmpl_context
from tg.i18n import ugettext as _, lazy_ugettext as l_
from tg.exceptions import HTTPFound
from tg import predicates
from unter import model
from unter.controllers.secure import SecureController
from unter.model import DBSession
from tgext.admin.tgadminconfig import BootstrapTGAdminConfig as TGAdminConfig
from tgext.admin.controller import AdminController

from unter.lib.base import BaseController
from unter.controllers.error import ErrorController
from unter.controllers.need import checkOneEvent, checkValidEvents

from unter.controllers.forms import NewAcctForm,AvailabilityForm,NeedEventForm

from unter.controllers.util import *
import unter.controllers.need as need
import unter.controllers.alerts as alerts
import unter.controllers.util as util

from sqlalchemy import or_,text

__all__ = ['RootController']

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
        tmpl_context.project_name = "unter"


    #==================================
    # Volunteer management.
    #==================================

    @expose('unter.templates.add_volunteer_start')
    def add_volunteer_start(self,form=None,error_msg=None):
        ''' Show the "Add a volunteer" page. '''
        if form is None:
            form = NewAcctForm()
        return dict(page='add_volunteer_start',form=form,url='/add_volunteer_post',error_msg=error_msg)

    @expose('unter.templates.add_volunteer_start')
    def add_volunteer_post(self,**kwargs):
        ''' Try to create a new volunteer. '''
        form = NewAcctForm(request.POST)
        if not form.validate():
            return self.add_volunteer_start(form=form)
            #redirect(lurl('/add_volunteer_start',dict(form=form)))
        else:
            thing = Thing()
            form.populate_obj(thing)
            thing.print()

            user_name = thing.user_name
            email = thing.email
            pwd = thing.pwd
            pwd2 = thing.pwd2
            print("Email is {}".format(email))

            existingUser = model.User.by_user_name(user_name)
            if existingUser is not None:
                return self.add_volunteer_start(form=form,error_msg='Account %s already exists'%user_name)
            existingUser = model.User.by_email_address(email)
            if existingUser is not None:
                return self.add_volunteer_start(form=form,error_msg='Email address %s is in use, please use a different one'%email)

            acct = model.User(user_name=user_name, email_address=email,display_name=form.display_name.data)
            acct.password = pwd
            DBSession.add(acct)
            acct = model.User.by_email_address(email)

            vinfo = model.VolunteerInfo(user_id=acct.user_id,description=form.description.data,
                    phone=form.phone.data,text_alerts_ok={True:1,False:0}[form.text_alerts_ok.data],
                    zipcode=form.zipcode.data)
            DBSession.add(vinfo)

            # Add the volunteer to the 'volunteers' group. To promote a
            # volunteer to a coordinator, add them to the 'coordinators' group
            # via the admin interface (/admin/ URL - you must be logged in as
            # 'manager' to use that).
            volGroup = DBSession.query(model.Group).filter_by(group_name='volunteers').first()
            volGroup.users.append(acct)

            if not request.identity:
                redirect(lurl('/login'),dict(message='Please log in and let us know when you are available.'))
            else:
                flash("Volunteer {} added".format(user_name))
                user,vinfo = self.getVolunteerIdentity()
                if 'manage_events' in [p.permission_name for p in user.permissions]:
                    page = '/coord_page'
                else:
                    # Hmm, we might not want to allow this :-/
                    page = '/volunteer_info'
                redirect(lurl(page,dict(message="Volunteer {} added".format(user_name))))

    @expose('unter.templates.add_availability_start')
    @require(predicates.not_anonymous())
    def add_availability_start(self,user_id,form=None):
        ''' Present the "add a time slot" form. '''
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

            redirect('/volunteer_info',dict(message=''))

    @expose('unter.templates.volunteer_info')
    @require(predicates.not_anonymous())
    def volunteer_info(self,user_id=None,**kwargs):
        if not request.identity:
            login_counter = request.environ.get('repoze.who.logins', 0) + 1
            redirect('/login',
                     params=dict(came_from="/volunteer_info",__logins=login_counter))
        user,vinfo = self.getVolunteerIdentity()
        requesting_user = user
        if user_id is not None:
            if predicates.has_permission('manage_events'):
                user,vinfo = self.getVolunteerIdentity(userId=user_id)
        if vinfo is None:
            # Not actually a volunteer - probably manager.
            redirect(lurl('/'),dict(message="No volunteer info for {}".format(user.user_name)))
        availabilities = [self.toRawAvailability(av) for av in user.volunteer_availability]
        events_responded = [vr.need_event for vr in user.volunteer_response if vr.need_event.complete == 0]
        events_responded = [toWrappedEvent(ev) for ev in events_responded]
        events_available = need.getAvailableEventsForVolunteer(model.DBSession,user)
        events_available = [toWrappedEvent(ev) for ev in events_available]

        return dict(user=user,volunteer_info=vinfo,
                requesting_user=requesting_user,
                availabilities=availabilities,
                events=events_responded,
                events_available=events_available,
                message='')

    @expose('unter.templates.all_volunteers')
    @require(predicates.has_permission('manage_events'))
    def all_volunteers(self):
        users = model.DBSession.query(model.User).all()
        users = [u for u in users if u.vinfo is not None]
        user,vinfo = self.getVolunteerIdentity()
        return dict(all_volunteers=users,user=user)

    @expose()
    @require(predicates.not_anonymous())
    def remove_availability(self,vaid,came_from=lurl('/volunteer_info')):
        av = model.DBSession.query(model.VolunteerAvailability).filter_by(vaid=vaid).first()
        if av is not None:
            model.DBSession.delete(av)
            flash("Available time removed.")
        else:
            flash("No such available time found.")
        redirect(came_from)

    @expose()
    def decommit(self,neid,came_from=lurl('/volunteer_info')):
        user,vinfo = self.getVolunteerIdentity()
        vr = model.DBSession.query(model.VolunteerResponse).filter_by(neid=neid).filter_by(user_id=user.user_id).first()
        if vr is not None:
            flash("Commitment cancelled. Thanks for letting us know!")
            need.decommit_volunteer(model.DBSession,vcom=vr)
        else:
            flash("No such commitment found for {}.".format(user.display_name))
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
    # Coordinator pages.
    #==================================

    @expose('unter.templates.coord_page')
    @require(predicates.has_permission('manage_events'))
    def coord_page(self,**kwargs):
        user,vinfo = self.getVolunteerIdentity()
        if user is None:
            redirect(lurl('/login'))
        events = model.DBSession.query(model.NeedEvent).filter_by(created_by=user).all()
        events = [toWrappedEvent(ev) for ev in events if ev.complete == 0]
        return dict(user=user,events=events,message='')

    def getVolunteerIdentity(self,userId=None):
        user,vinfo = None,None
        if userId is None:
            ''' Get the logged-in user's volunteer identity. '''
            if request.identity is not None and 'repoze.who.userid' in request.identity:
                userid = request.identity['repoze.who.userid']
                user = model.User.by_user_name(userid)
                vinfo = user.vinfo
                print("user.vinfo = {}".format(vinfo))
        else:
            ''' Get the identity for the given user. '''
            user = model.DBSession.query(model.User).filter_by(user_id=userId).first()
            if user is not None:
                vinfo = user.vinfo
        return user,vinfo

    #==================================
    # Need event management.
    #==================================

    @expose()
    def respond(self,neid):
        user,vinfo = self.getVolunteerIdentity()
        if user is None:
            redirect(lurl('/login'))
        vresp = model.VolunteerResponse(user_id=user.user_id,neid=neid)
        model.DBSession.add(vresp)
        redirect(lurl('/volunteer_info',dict(user_id=user.user_id,message='')))

    @expose('unter.templates.add_need_event_start')
    @require(predicates.has_permission('manage_events'))
    def add_need_event_start(self,form=None,**kwargs):
        ''' Present the "add a need event" form. '''
        if form is None:
            form = NeedEventForm()
        return dict(page='add_need_event_start',form=form,url='/add_need_event_post')

    @expose('unter.templates.add_need_event_start')
    @require(predicates.has_permission('manage_events'))
    def add_need_event_post(self,**kwargs):
        form = NeedEventForm(request.POST)
        for fld in form:
            print("Form {} = {}".format(fld.name,fld.data))
        if not form.validate():
            print("Need event data is NOT valid: {}".format(form.errors))
            return self.add_need_event_start(form=form)
        else:
            print("Need event data is valid")
            obj = Thing()
            form.populate_obj(obj)
            obj.print("NeedEvent:")

            user,vinfo = self.getVolunteerIdentity()

            dt = datetime.datetime(obj.date_of_need.year,
                    obj.date_of_need.month,
                    obj.date_of_need.day,
                    hour=12)

            nev = model.NeedEvent(ev_type=int(obj.ev_type),
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
        user,vinfo = self.getVolunteerIdentity()
        isCoordinator = False
        if user is not None:
            print("user.permissions: {}".format(user.permissions))
            isCoordinator = 'manage_events' in [perm.permission_name for perm in user.permissions]
        return dict(user=user,vinfo=vinfo,isCoordinator=isCoordinator,evs=evs,complete=completed)

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
        user,vinfo = self.getVolunteerIdentity()
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

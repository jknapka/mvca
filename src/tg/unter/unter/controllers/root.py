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

from unter.controllers.forms import NewAcctForm,AvailabilityForm,NeedEventForm

from twilio.rest import Client as TwiCli

__all__ = ['RootController']

def minutesPastMidnight(tm):
    print("tm is a {}".format(tm.__class__.__name__))

    return 60*tm.hour+tm.minute

def minutesPastMidnightToTimeString(mpm):
    hour = int(mpm/60)
    mins = mpm % 60
    return "{}:{:02d}".format(hour,mins)

class Thing(object):
    ''' A generic ocntainer in which to unpack form data. '''

    def print(self,label="Thing:"):
        print(label)
        for key in self.__dict__.keys():
            print("  {}={}".format(key,self.__dict__[key]))

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
    def add_volunteer_start(self,form=None):
        ''' Show the "Add a volunteer" page. '''
        if form is None:
            form = NewAcctForm()
        return dict(page='add_volunteer_start',form=form,url='/add_volunteer_post')

    @expose('unter.templates.add_volunteer_start')
    def add_volunteer_post(self,**kwargs):
        ''' Try to create a new volunteer. '''
        print(('{}\n'*len(kwargs)).format(*['{}={}'.format(key,kwargs[key]) for key in kwargs]))
        form = NewAcctForm(request.POST)
        if not form.validate():
            print("form.errors = {}".format(form.errors))
            return self.add_volunteer_start(form=form)
            #redirect(lurl('/add_volunteer_start',dict(form=form)))
        else:
            print("Form data is valid.")

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
                redirect(url('/acctError'), dict(message='Account %s already exists'%user_name,
                                     user_name=user_name, email=email))
            existingUser = model.User.by_email_address(email)
            if existingUser is not None:
                redirect(url('/acctError'), dict(message='Email address %s is in use, please us a different one'%email,
                                     user_name=user_name, email=email))
            if pwd != pwd2:
                redirect(url('/acctError'), dict(message='Oops! The passwords do not match',
                    user_name=user_name, email=email))
            acct = model.User(user_name=user_name, email_address=email)
            acct.password = pwd
            DBSession.add(acct)
            acct = model.User.by_email_address(email)

            vinfo = model.VolunteerInfo(user_id=acct.user_id,description=form.description.data,
                    phone=form.phone.data,text_alerts_ok={True:1,False:0}[form.text_alerts_ok.data],
                    zipcode=form.zipcode.data)
            DBSession.add(vinfo)

            redirect(lurl('/login'),dict(message='Please log in and let us know when you are available.'))

    @expose('unter.templates.add_availability_start')
    def add_availability_start(self,user_id,form=None):
        ''' Present the "add a time slot" form. '''
        if form is None:
            form = AvailabilityForm(user_id=user_id)
        return dict(page='add_availability_start',form=form,url='/add_availability_post')

    @expose('unter.templates.add_availability_start')
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

            redirect('/volunteer_info',dict(user_id=obj.user_id))

    @expose('unter.templates.volunteer_info')
    def volunteer_info(self,user_id,**kwargs):
        user = model.User.by_user_id(user_id)
        vinfo = user.volunteer_info[0]
        availabilities = [self.toRawAvailability(av) for av in user.volunteer_availability]

        return dict(user=user,volunteer_info=vinfo,availabilities=availabilities)

    def toRawAvailability(self,av):
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
        return result

    #==================================
    # Need event management.
    #==================================

    @expose('unter.templates.add_need_event_start')
    def add_need_event_start(self,form=None,**kwargs):
        ''' Present the "add a need event" form. '''
        if form is None:
            form = NeedEventForm()
        return dict(page='add_need_event_start',form=form,url='/add_need_event_post')

    @expose('unter.templates.add_need_event_start')
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
                    notes=obj.notes)
            DBSession.add(nev)

            self.smsJoe(obj.volunteer_count,minutesPastMidnight(obj.time_of_need),int(obj.ev_type))

            redirect(lurl('/need_events'))

    def smsJoe(self,n_vols,at_time,ev_type):
        sid = 'xxxx'
        auth_tok = 'xxx'
       
        def evTypeToString(evt):
            return {0:"take people to the airport",
                    1:"take people to the bus station",
                    2:"interpeter services"}[evt]

        cli = TwiCli(sid,auth_tok)
        message = cli.messages.create(body="We have a need for {} volunteer(s) at {}. Purpose: {}. Can you help?".format(n_vols,minutesPastMidnightToTimeString(at_time), evTypeToString(ev_type)),
                from_="+19159743306",
                to="+19155495098")
        print(message.sid)

    @expose()
    def need_events(self,**kwargs):
        return "Placeholder"

    @expose('json')
    def check_need_events(self,ev_id=None):
        pass

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
        userid = request.identity['repoze.who.userid']
        flash(_('Welcome back, %s!') % userid)

        user = model.User.by_user_name(userid)

        for attr in request.identity:
            print("request.identity[{}] = {}".format(attr,request.identity[attr]))

        # Do not use tg.redirect with tg.url as it will add the mountpoint
        # of the application twice.
        came_from = lurl('/volunteer_info',params=dict(user_id=user.user_id))
        return HTTPFound(location=came_from)

    @expose()
    def post_logout(self, came_from=lurl('/')):
        """
        Redirect the user to the initially requested page on logout and say
        goodbye as well.

        """
        flash(_('We hope to see you soon!'))
        return HTTPFound(location=came_from)

'''
Utility functions used in various places.
'''
import datetime as dt
import logging

import tg

from unter.controllers.i18n import FAKE_ as _, FAKEl_ as l_

from unter import model

def debugTest(msg):
    logging.getLogger('unter.test').debug(msg)

def isUserManager(user):
    perms = [p.permission_name for p in user.permissions]
    return 'manage' in perms or 'manage_events' in perms

def evTypeToString(evt):
    return {0:_("take people to the airport"),
            1:("take people to the bus station"),
            2:("interpeter services")}[evt]

def minutesPastMidnight(tm):
    print("tm is a {}".format(tm.__class__.__name__))

    return 60*tm.hour+tm.minute

def minutesPastMidnightToTimeString(mpm):
    hour = int(mpm/60)
    mins = mpm % 60
    return "{}:{:02d}".format(hour,mins)

class Thing(object):
    ''' A generic container in which to unpack form data. '''

    def print(self,label=l_("Thing:")):
        printDict(self.__dict__)

def printDict(kwargs,label="kwargs:"):
    print(label)
    print(('  {}\n'*len(kwargs)).format(*['{}={}'.format(key,kwargs[key]) for key in kwargs]))

def toWrappedEvent(ev,now=None):
    thing = Thing()
    thing.ev = ev
    date = dt.date.fromtimestamp(ev.date_of_need)
    if now is not None:
        if date < now:
            ev.complete = 1
    thing.date_str = "{:02d}/{:02d}/{:04d}".format(date.month,date.day,date.year)
    thing.time_str = minutesPastMidnightToTimeString(ev.time_of_need)
    thing.ev_str = evTypeToString(ev.ev_type)
    thing.complete = {1:'Yes',0:'No'}[ev.complete]
    thing.last_alert_time = dt.datetime.fromtimestamp(ev.last_alert_time).ctime()
    return thing

def createUser(user_name="test",email="test@test.test",
        phone="0010010001",desc="Test user",zipcode="79900",
        display_name=None,
        groups=[]):
    if display_name is None:
        display_name = user_name[0].upper()+user_name[1:] 
    u = model.User()
    u.user_name = user_name
    u.display_name = display_name
    u.email_address = email
    v = model.VolunteerInfo()
    v.phone = phone
    v.description = desc
    v.sipcode = zipcode
    u.vinfo = v

    for group in groups:
        g = model.DBSession.query(model.Group).filter_by(group_name=group).first()
        g.users.append(u)

    model.DBSession.add(u)
    return u

def createAvailability(user,days=['m','t','w','th','f','s','su'],
        start_time=6*60+3,
        end_time=18*60+4):
    tf={True:1,False:0}
    av = model.VolunteerAvailability(start_time=start_time,
            end_time=end_time,
            dow_monday=tf['m' in days],
            dow_tuesday=tf['t' in days],
            dow_wednesday=tf['w' in days],
            dow_thursday=tf['th' in days],
            dow_friday=tf['f' in days],
            dow_saturday=tf['s' in days],
            dow_sunday=tf['su' in days])
    av.user = user
    model.DBSession.add(av)
    return av

def createEvent(created_by,
        ev_type=model.NeedEvent.EV_TYPE_BUS,
        date_of_need=None,
        time_of_need=10*60+19,
        duration=63,notes=l_("DEFAULT NOTE"),
        volunteer_count=1,
        affected_persons=2,
        location=l_("Nowhere"),
        complete=0):
    if date_of_need is None:
        date_of_need = dt.date.today() + dt.timedelta(days=1)
    vne = model.NeedEvent()
    vne.ev_type = ev_type
    vne.date_of_need = date_of_need.timestamp()
    vne.time_of_need = time_of_need
    vne.duration = duration
    vne.volunteer_count = volunteer_count
    vne.affected_persons = affected_persons
    vne.location = location
    vne.notes = notes
    vne.complete = complete
    vne.created_by = created_by
    model.DBSession.add(vne)
    return vne

def createResponse(volName,evNotes):
    veronica = getUser(model.DBSession,volName)
    ev = model.DBSession.query(model.NeedEvent).filter_by(notes=evNotes).first()
    vr = model.VolunteerResponse()
    vr.user = veronica
    vr.need_event = ev
    model.DBSession.add(vr)

def getUser(uname):
    return model.DBSession.query(model.User).filter_by(user_name=uname).first()

def setupTestUsers():
    coords = model.DBSession.query(model.Group).filter_by(group_name='coordinators').first()
    vols = model.DBSession.query(model.Group).filter_by(group_name='volunteers').first()

    carla = model.User(user_name='carla',email_address='carla@nowhere.net',display_name='Carla',password='carla')
    carla_vi = model.VolunteerInfo(zipcode='79900',phone='9150010001',description='Carla the Coordinator')
    carla.vinfo = carla_vi
    coords.users.append(carla)
    model.DBSession.add(carla)
    
    phone = 9150010002
    for uname in ('victor','veronica','velma','vernon','vaughn'):
        u = model.User(user_name=uname,email_address=uname+'@nowhere.net',display_name=uname[0].upper()+uname[1:],password=uname)
        v = model.VolunteerInfo(zipcode='79900',phone=""+str(phone),description=u.display_name+' the Volunteer')
        u.vinfo = v
        vols.users.append(u)
        model.DBSession.add(u)
        phone += 1

def setupTestAvailabilities():
    veronica = getUser('veronica')
    velma = getUser('velma')
    # Veronica is available 10AM to 2PM on all days of the week.
    # (This saves us from having to create events on particular days
    # of the week.)
    av = createAvailability(user=veronica,
            start_time=10*60,end_time=14*60,
            days=["m","t","w","th","f","s","su"])

    # Velma is available noon to 3 on all days of the week.
    av = createAvailability(user=velma,
            start_time=12*60,end_time=15*60,
            days=["m","t","w","th","f","s","su"])

def setupTestEvents():
    # Events:
    
    carla = getUser('carla')

    # A bus and an airport for Veronica.
    createEvent(created_by=carla,
            ev_type=model.NeedEvent.EV_TYPE_BUS,
            date_of_need=dt.datetime.now() + dt.timedelta(days=1),
            time_of_need=10*60+30,
            location="Veronica only bus 1 location",
            notes="Veronica only bus 1")

    createEvent(created_by=carla,
            ev_type=model.NeedEvent.EV_TYPE_AIRPORT,
            date_of_need=dt.datetime.now() + dt.timedelta(days=2),
            time_of_need=10*60+33,
            location="Veronica only airport location",
            notes="Veronica only airport")

    # A bus that overlaps the other bus for Veronica:
    createEvent(created_by=carla,
            ev_type=model.NeedEvent.EV_TYPE_BUS,
            date_of_need=dt.datetime.now() + dt.timedelta(days=1),
            time_of_need=10*60+45,
            location="Veronica only bus 2 location",
            notes="Veronica only bus 2")

    # A bus for Velma.
    createEvent(created_by=carla,
            ev_type=model.NeedEvent.EV_TYPE_BUS,
            date_of_need=dt.datetime.now() + dt.timedelta(days=1),
            time_of_need=14*60+3,
            duration=20,
            location="Velma only bus location",
            notes="Velma only bus")

    # An airport that either Veronica or Velma could do.
    createEvent(created_by=carla,
            ev_type=model.NeedEvent.EV_TYPE_AIRPORT,
            date_of_need=dt.datetime.now() + dt.timedelta(days=1),
            time_of_need=12*60+23,
            location="Veronica or Velma airport location",
            notes="Veronica or Velma airport")

__all__ = ['evTypeToString','minutesPastMidnight','minutesPastMidnightToTimeString',
    'Thing','printDict','toWrappedEvent','setupTestUsers','setupTestAvailabilities',
    'setupTestEvents','debugTest']

'''
Utility functions used in various places.
'''
import datetime

from unter import model

def evTypeToString(evt):
    return {0:"take people to the airport",
            1:"take people to the bus station",
            2:"interpeter services"}[evt]

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
        printDict(self.__dict__)

def printDict(kwargs,label="kwargs:"):
    print(label)
    print(('  {}\n'*len(kwargs)).format(*['{}={}'.format(key,kwargs[key]) for key in kwargs]))

def toWrappedEvent(ev,now=None):
    thing = Thing()
    thing.ev = ev
    date = datetime.date.fromtimestamp(ev.date_of_need)
    if now is not None:
        if date < now:
            ev.complete = 1
    thing.date_str = "{:02d}/{:02d}/{:04d}".format(date.month,date.day,date.year)
    thing.time_str = minutesPastMidnightToTimeString(ev.time_of_need)
    thing.ev_str = evTypeToString(ev.ev_type)
    thing.complete = {1:'Yes',0:'No'}[ev.complete]
    thing.last_alert_time = datetime.datetime.fromtimestamp(ev.last_alert_time).ctime()
    return thing

def setupTestUsers(dbsession):
    coords = dbsession.query(model.Group).filter_by(group_name='coordinators').first()
    vols = dbsession.query(model.Group).filter_by(group_name='volunteers').first()

    carla = model.User(user_name='carla',email_address='carla@nowhere.net',display_name='Carla',password='carla')
    carla_vi = model.VolunteerInfo(zipcode='79900',phone='9150010001',description='Carla the Coordinator')
    carla.vinfo = carla_vi
    coords.users.append(carla)
    dbsession.add(carla)
    
    phone = 9150010002
    for uname in ('victor','veronica','velma','vernon','vaughn'):
        u = model.User(user_name=uname,email_address=uname+'@nowhere.net',display_name=uname[0].upper()+uname[1:],password=uname)
        v = model.VolunteerInfo(zipcode='79900',phone=""+str(phone),description=u.display_name+' the Volunteer')
        u.vinfo = v
        vols.users.append(u)
        dbsession.add(u)
        phone += 1

__all__ = ['evTypeToString','minutesPastMidnight','minutesPastMidnightToTimeString',
    'Thing','printDict','toWrappedEvent','setupTestUsers']

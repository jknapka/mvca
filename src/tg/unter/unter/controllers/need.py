'''
Code for matching need events with volunteers.
'''
import datetime as dt

import unter.model as model
import unter.controllers.alerts as alerts

def checkOneEvent(dbsession,ev_id,honorLastAlertTime=True):
    print("Checking need event {}".format(ev_id))
    nev = dbsession.query(model.NeedEvent).filter_by(neid=ev_id).first()
    vols = getAlertableVolunteers(dbsession,nev)
    alerts.sendAlerts(vols,nev,honorLastAlertTime=honorLastAlertTime)
    dbsession.flush()

def checkValidEvents(dbsession,when):
    print("Checking need events at {}".format(when))

def getDowCheck(nev):
    '''
    Get a function that will check VolunteerAvailability
    objects to see if they match the day-of-week of nev.
    '''
    dow = dt.datetime.fromtimestamp(nev.date_of_need).weekday()

    return {
            0:lambda x: x.dow_monday == 1,
            1:lambda x: x.dow_tuesday == 1,
            2:lambda x: x.dow_wednesday == 1,
            3:lambda x: x.dow_thursday == 1,
            4:lambda x: x.dow_friday == 1,
            5:lambda x: x.dow_saturday == 1,
            6:lambda x: x.dow_sunday == 1,
            }[dow]

def getAvailableVolunteers(dbsession,nev):
    '''
    Get volunteers who have indicated they are available at the
    time and for the duration of the given event. This method
    does not consider existing commitments, it only looks at
    availabilities.
    '''
    result = []

    allVols = dbsession.query(model.User).all()
    dowCheck = getDowCheck(nev)
    for vol in allVols:
        if 'respond_to_need' not in [p.permission_name for p in vol.permissions]:
            continue
        for avail in vol.volunteer_availability:
            if dowCheck(avail):
                # Available on the day-of-week.
                if avail.start_time <= nev.time_of_need and\
                        avail.end_time >= nev.time_of_need+nev.duration:
                    result.append(vol)

    return result

def ev2Str(ev):
    date = dt.datetime.fromtimestamp(ev.date_of_need)
    time = "{:02d}:{:02d}".format(int(ev.time_of_need / 60),int(ev.time_of_need%60))
    duration = ev.duration
    return "{}/{}/{} {} {}".format(date.year,date.month,date.day,time,duration)

def overlappingEvents(ev1,ev2):
    result = None
    ev1Date = dt.datetime.fromtimestamp(ev1.date_of_need)
    ev2Date = dt.datetime.fromtimestamp(ev2.date_of_need)
    if ev1Date.year != ev2Date.year or \
        ev1Date.month != ev2Date.month or \
        ev1Date.day != ev2Date.day:
            result = False
    else:
        ev1start = ev1.time_of_need
        ev1end = ev1.time_of_need + ev1.duration
        ev2start = ev2.time_of_need
        ev2end = ev2.time_of_need + ev2.duration
        if ev1start > ev2start and ev1start < ev2end:
            result = True
        if ev1end > ev2start and ev1end < ev2end:
            result = True
        if ev2start > ev1start and ev2start < ev1end:
            result = True
        if ev2end > ev1start and ev2end < ev1end:
            result = True
    return result

def getUncommittedVolunteers(dbsession,nev,vols):
    '''
    From a list of available volunteers vols, get those who have no
    conflicting commitments with need event nev.
    '''
    result = []

    for vol in vols:
        available = True
        for r in vol.volunteer_response:
            rnev = r.need_event
            if overlappingEvents(nev,rnev):
                # Not available.
                available = False
                break
        if available:
            result.append(vol)

    return result

def getAlertableVolunteers(dbsession,nev):
    return getUncommittedVolunteers(dbsession,nev,getAvailableVolunteers(dbsession,nev))

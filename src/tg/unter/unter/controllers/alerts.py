'''
Utilities for sending alerts.
'''
import datetime as dt

from twilio.rest import Client as TwiCli

# Alert no more than every 4 hours for any particular event.
MIN_ALERT_SECONDS = 3600 * 4

SMS_ENABLED = False
EMAIL_ENABLED = False

def sendAlerts(volunteers,nev,honorLastAlertTime=True):
    '''
    Send alerts to the given volunteers for need event nev.
    '''
    if honorLastAlertTime:
        now = dt.datetime.now().timestamp()
        if now - MIN_ALERT_SECONDS < nev.last_alert_time:
            print("NOT alerting for need event {} - it was alerted recently.".format(\
                    nev.neid))
            return False
    for vol in volunteers:
        print("ALERTING {} for need event {}".format(vol.user_name,nev.neid))
        if SMS_ENABLED:
            if vol.vinfo.text_alerts_ok == 1:
                sehdSmsForEvent(nev,vol)
        if EMAIL_ENABLED:
            sendEmailForEvent(nev,vol)
    nev.last_alert_time = int(dt.datetime.now().timestamp())
    return True

def sendEmailForEvent(nev,vol,source="MVCA"):
    print("FIX ME: implement email. Trying to send email to {} for neid {}".format(\
            vol.email_address,nev.neid))

def makeValidSMSPhoneNumber(num):
    if len(num) == 7:
        # Assume El Paso :-(
        num = "915"+num
    if num[:2] != "+1":
        num = "+1"+num
    return num

def sendSmsForEvent(nev,vol,source="MVCA"):
    destNumber = makeValidSMSPhoneNumber(vol.vinfo.phone)
    n_vols = nev.volunteer_count
    at_time=nev.time_of_need
    ev_type = nev.ev_type
    location = nev.location
    link = "{}/respond?user_id={}&neid=P{".format(MVCA_SITE,vol.user_id,nev.neid)
    msg = "This is {}. We have a need for {} volunteer(s) at {}. Purpose: {}. "\
            +"Location: {}. Can you help? Click link to commit: {}".format(source,\
            n_vols,\
            minutesPastMidnightToTimeString(at_time),\
            evTypeToString(ev_type),\
            location,link)
    sendSMS(msg,destNumber=destNumber)

def sendSMS(message,sourceNumber="+10159743307",destNumber="+19155495098"):
    sid = 'xxxx'
    auth_tok = 'xxxx'
   
    cli = TwiCli(sid,auth_tok)
    message = cli.messages.create(body=message,
            from_=sourceNumber,
            to=destNumber)
    print(message.sid)


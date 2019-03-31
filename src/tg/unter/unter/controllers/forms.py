'''
Forms used by the Unter web service.
'''
import urllib.parse as urls
import wtforms as wtf
import wtforms_components as wtfc
import re
import datetime

SAFE_USER_NAME_RE = re.compile('^[A-Za-z1-9]*$')
SAFE_EMAIL_RE = re.compile('^[^@]+@[a-zA-Z0-9-.]+.[a-zA-Z0-9-.]+[^.]$')
SAFE_DISPLAY_NAME_RE = re.compile('^[A-Za-z0-9 ]*$')
SAFE_DESCRIPTION_RE = re.compile('^[-.,A-Za-z0-9 ]*$')
MIN_PWD_LEN = 1

class NeedEventForm(wtf.Form):
	''' WTForm definition to add a need event. '''
	date_of_need = wtfc.DateField("Date")
	time_of_need = wtfc.TimeField("Time")
	ev_type = wtf.SelectField("Type of Need",
			choices=[("0","Airport"),("1","Bus station"),("2","Interpreter services")])
	duration = wtf.DecimalField("Estimated Duration (minutes)")
	volunteer_count = wtf.DecimalField("Number of Volunteers Needed")
	affected_persons = wtf.DecimalField("Number of People With Need")
	location = wtf.TextField("Location")
	notes = wtf.TextField("Notes")

	def validate_location(self,field):
		if not isSafeDescription(field.data):
			raise wtf.ValidationError("Only letters, numbers, spaces, commas, and periods are allowed here.")
	
	def validate_notes(self,field):
		self.validate_location(field)

class AvailabilityForm(wtf.Form):
	''' WTForms definition for adding volunteer availability. '''
	user_id = wtf.HiddenField()
	start_time = wtfc.TimeField("Earliest available time",default=datetime.time(hour=6,minute=0))
	end_time = wtfc.TimeField("Latest available time",default=datetime.time(hour=18,minute=0))
	dow_sunday = wtf.BooleanField("Sunday",default=True)
	dow_monday = wtf.BooleanField("Monday",default=True)
	dow_tuesday = wtf.BooleanField("Tuesday",default=True)
	dow_wednesday = wtf.BooleanField("Wednesday",default=True)
	dow_thursday = wtf.BooleanField("Thursday",default=True)
	dow_friday = wtf.BooleanField("Friday",default=True)
	dow_saturday = wtf.BooleanField("Saturday",default=True)

class NewAcctForm(wtf.Form):
	''' WTForms definition for adding a new account. '''
	user_name = wtf.TextField('User Name')
	display_name = wtf.TextField('Display Name')
	pwd = wtf.PasswordField('Password')
	pwd2 = wtf.PasswordField('Confirm Password')
	email = wtf.TextField('Email Address')
	phone = wtf.TextField('Phone number')
	text_alerts_ok = wtf.BooleanField('OK to send text alerts?')
	zipcode = wtf.TextField('Zip code')
	description = wtf.TextField('Brief introduction')

	def validate_display_name(self,field):
		if not isSafeDisplayName(field.data):
			raise wtf.ValidationError("Only letters, numbers and spaces are allowed here.")

	def validate_description(self,field):
		if not isSafeDescription(field.data):
			raise wtf.ValidationError("Only letters, numbers, periods, and commas are allowed here.")

	def validate_user_name(self, field):
		if not isSafeUserName(field.data):
			raise wtf.ValidationError("Your user name can only contain English letters and numbers.")
	
	def validate_pwd(self, field):
		if field.data != self.pwd2.data:
			raise wtf.ValidationError("The paswords do not match.")
		if len(field.data) < MIN_PWD_LEN:
			raise wtf.ValidationError("Your password must be at least {} characters long.".format(MIN_PWD_LEN))
	
	def validate_email(self, field):
		if not isSafeEmail(field.data):
			raise wtf.ValidationError("This does not appear to be a valid email address.")
	
def isSafe(s,re):
	m = re.match(s)
	return m is not None

def isSafeUserName(uname):
	return isSafe(uname,SAFE_USER_NAME_RE)

def isSafeEmail(email):
	return isSafe(email,SAFE_EMAIL_RE)

def isSafeDisplayName(dn):
	return isSafe(dn,SAFE_DISPLAY_NAME_RE)

def isSafeDescription(dsc):
	return isSafe(dsc,SAFE_DESCRIPTION_RE)

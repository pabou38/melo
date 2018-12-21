#!/usr/bin/python

import json
import sys
import imaplib
import getpass
import email
import email.header
import datetime
import pprint
from bs4 import BeautifulSoup
import base64
import binascii
import re
# pip install markdown (apt-get install markdown is CLI, cannot import)
#from markdown import markdown
import chardet
import re

# enable Autoriser les applications qui utilisent la .. dans console yahoo

my_name = "melo meli"


"""
Doesn't work with two-way verification unless:
https://www.google.com/settings/security/lesssecureapps
For two-way verification the best and recommended solution is to generate an app password 
https://security.google.com/settings/security/apppasswords.
"""

"""
# absolute path for systemctl 
def get_cred():
	with open('/home/pi/imap/config_yahoo.json') as json_data_file:
		data = json.load(json_data_file)
	for item in data['cred']:
		print item
	return(data['cred'][0], data['cred'][1])
"""

def isBase64(s):
	try:
		return base64.b64encode(base64.b64decode(s)) == s
	except Exception:
		return False

# called from main. main call crypto before
def init_imap(mail,pa):
	global M
	M = imaplib.IMAP4_SSL('imap.mail.yahoo.com',993)
	#(mail,pa)= get_cred()
	try:
		rv, data = M.login(mail, pa)
	except imaplib.IMAP4.error as e:
		print "IMAP LOGIN FAILED!!! " , str(e)
		#(False, '[AUTHENTICATIONFAILED] LOGIN Invalid credentials')
		return (False,str(e))


	if rv == "OK":
		#(True, ['LOGIN completed'])
		print "rv, auth data", rv,data
		return (True,data)

# returns number of messages even before search ?
def select_mailbox(box):
	global M
	# examine , no change permitted
	#M.select(readonly =1) Inbox
	rv, data = M.select(box)
	if rv != 'OK':
		print "cannot select INBOX"
		print "rv, data: ", rv,data
		return (False,data)
	else:
		print "rv, data: ", rv,data
		return (True,data)

def list_mailboxes():
	global M
	rv, mailboxes = M.list()
	if rv == 'OK':
		print "found mailboxes:"
		#print mailboxes
		return (True)
	else:
		return (False)

###  uid  search, fetch, store
#Don't mix message sequence numbers (fetch, store, search) with UIDs (uid fetch, uid store, uid search)

def search_mailbox():
	global M
	print "Processing INBOX, searching, return id_list...\n"
	# status, response = imap.search(None, '(UNSEEN)', '(FROM "%s")' % (sender_of_interest))
	# result, data = mail.search(None, '(BEFORE "'+str(bedate)+'")')
	# '(UNSEEN SUBJECT %s)' %(sub)
	#rv, data = M.search(None, "ALL")
	print "only UNSEEN messages"
	rv, data = M.search(None, "UNSEEN")
	#rv, data = M.uid('search', None, "ALL")
	# uid store flag does not work with Yahoo IMAP. ok with gmail
	# search without uid. data is ['1 2 3 4 5 6 7 8 ']
	# with uid ['5 6 13 15 16 17 ']

	#rv, data = M.search(None, "UNSEEN")
	if rv != 'OK':
		print "No messages found!"
		return(False,[])
	id_list= data[0].split()
	print id_list
	return (True,id_list) # list of string


#OK
#['5 (FLAGS (\\Deleted \\Seen $NotJunk))']
# return flag and tuple of boolean (seen, deleted)
def fetch_email_flag(num):
	global yahoo_mail
	rv, data = M.fetch(num, '(FLAGS)')
	dele=seen=False
	if rv != 'OK':
		print "ERROR getting message flag", num
		return(False, (dele,seen))
	else:
		# check if seen or deleted
		match = re.search(r'Seen',data[0])
		if match is not None:
			seen=True
			#print match.group()

		match = re.search(r'Delete',data[0])
		if match is not None:
			dele=True
			#print match.group()

		return(True, (dele,seen))



#Fetch (parts of) messages. message_parts should be a string of message part names enclosed within parentheses, eg: "(UID BODY[TEXT])". Returned data are tuples of message part envelope and data.
def fetch_email_headers(num):
	global yahoo_mail
	#print "\nFetching Email header: ", num
	print num

# id_list[-1] latest
#https://tools.ietf.org/html/rfc3501#section-6.4.5
# update global yahoo_mail dict and return value to hook

# peek does not seen seen ?
	rv, data = M.fetch(num, '(BODY.PEEK[HEADER])') # header only
	#rv, data = M.uid('fetch', num, '(BODY.PEEK[HEADER])') # header only

	if rv != 'OK':
		print "ERROR getting message header", num
		return(False, " ", " ", " " )

	raw_email = data[0][1]
	# data type list, lot of lines
	#https://docs.python.org/2/library/email.parser.html

	raw_email_string = raw_email.decode('utf-8')

	msg = email.message_from_string(raw_email_string)
	# msg type instance , From, received, .. all headers and bodies all headers, list of tuple
	# print msg.items()

	# decode is a tuple (subject, None or 'utf-8')

	decode = email.header.decode_header(msg['Subject'])[0]	
	subject = decode[0]
	# type str
	#print subject, type(subject), decode[1]
	#  P2(P3) str(bytes) unicode(str)
	if isinstance(subject, str):
		#print "str type, decode as utf"
		subject = subject.decode('utf-8')
		#print "decoded" , type(subject)

	decode = email.header.decode_header(msg['From'])[0]
	from_add = decode[0]
	# type str
	#print from_add, type(from_add),  decode[1]
	if isinstance(from_add, str):
		#print "str type, decode as utf"
		from_add = from_add.decode('utf-8')
		#print "decoded"  , type(from_add)

	to_add = msg ['To']

	#print 'Raw Date:', msg['Date'] # type str
        # Now convert to local date-time
	date_tuple = email.utils.parsedate_tz(msg['Date'])
	# type tuple (2018, 11, 16, 11, 0, 45, 0, 1, -1, 3600)
	if date_tuple:
		local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
		#print "Local Date:", local_date.strftime("%a, %d %b %Y %H:%M:%S")	

		# local_date 2018-11-17 16:31:26
		# Local Date: Sat, 17 Nov 2018 16:31:26

	# dict, value is list vs tuple as we want to change it later. add text

	#print "\nFetching Email flag: ", num
	(flag,(dele,seen)) = fetch_email_flag(num)
	if not flag:
		print "error getting flag: ", num 
		# default false, false
	#type, data = M.store(num, '+FLAGS', '\\Seen')
	return(True, from_add, to_add, subject, (dele,seen)) 

def fetch_email_body(num):
	global email
	text_list=[]

#https://docs.python.org/2/library/email.message.html
# non multipart .get_payload return string multipart,  get_payload return list of message	

	rv, data = M.fetch( num, '(RFC822)')
	#rv, data = M.uid('fetch', num, '(RFC822)')

	if rv != 'OK':
		print "ERROR getting message body", num
		return(False, [])

	raw_email = data[0][1]
	if not raw_email:  # ceinture et bretelles
		return[]
	#raw_email_string = raw_email.decode('utf-8')    will decode payload as utf-8 anyway
	msg = email.message_from_string(raw_email)

	for part in msg.walk(): # recursive

		print "==========  getting parts for message: ", num
		content_type=part.get_content_type()

		main_type=part.get_content_maintype()
		print "main type: %s , content_type: %s, is_multipart: %r"  %(main_type , content_type, part.is_multipart())
		# ismultipart can be true for non "multipart" main type
		charset =part.get_content_charset()
		if charset is None:
			print "unknown charset"
		else:
			print "charset: " , charset

#Optional decode is a flag indicating whether the payload should be decoded or not, according to the 
#Content-Transfer-Encoding header. When True and the message is not a multipart, the payload will be decoded 
#if this header value is quoted-printable or base64. If some other encoding is used, 
#or Content-Transfer-Encoding header is missing, or if the payload has bogus base64 data, the payload 
#is returned as-is (undecoded). If the message is a multipart and the decode flag is True, then None is returned.
#The default for decode is False.

#https://stackoverflow.com/questions/43824650/encoding-issue-decode-quoted-printable-string-in-python
# quotable printable string: unicode coded as ascii eg =AC=E9  .

		if content_type == 'text/plain':
			print "=======>>>> got a text plain payload "
			# return Return the current payload, which will be a list of messages or a string is_multipart 
			payload = part.get_payload(decode=True) # string or list of messages. true toi decode quotable printable string. otherwize shouw up in  text
			print chardet.detect(payload)
			if isinstance(payload, str):
				print "payload str"
			else:
				print "payload not str"
			# print type(payload) ERROR TypeError: 'str' object is not callable

# let ^^  0xe2 80 90  U+2019 rigth single quote

			if payload.find(' ') == -1: # check if base 64 
				print("base64 ignored")
				text_list.append(u"ignored binary") # space otherwise says dot
			else:
				try:
					text = payload.decode('utf-8')
					print "text decoded as utf " 
				except Exception as e:
					print "Exception decoding payload as uft8: " , str(e)
				#soup= BeautifulSoup(payload)
				#text = soup.get_text()
				#html = markdown(payload)
				#html = payload # to not use markdown. also normally not needed. this is not html 
				#soup = BeautifulSoup(html,"html.parser")
				#text = ''.join(soup.findAll(text=True))
				text_list.append(text)
		else:
			type = re.sub(r'/'," ",content_type)
			text_list.append(u"ignored %s" %(type.split(' ')[1]))
	return (True, text_list) # list of text/ascii payloads.

# uid does not work with yahoo
#  \Seen \Unseen
def set_delete_flag(uid):
	print "set delete flag: " , uid
	#M.uid('STORE', uid, '+FLAGS', '(\\Deleted)')
	s =M.store(uid, '+FLAGS', '\\Deleted')
	return s
		#('OK', ['5'])

# close does purge
def exit_imap():
	global M
	print "close and logout"
	#M.expunge()
	M.close()
	M.logout()



def fetch_all_headers():
	global id_list

	# id_list: list of string '1', '2' ... or
	for num in reversed(id_list): # reverse order . latest first
		print "%%%%%%%%%%%%%%%% Fetching headers", num
		(flag,from_add,to_add,subject,(dele,seen)) = fetch_email_headers(num) 
		if flag:
			print "FROM: ",from_add
			print "SUBJECT: ",subject
			print "FLAGS (deleted, seen): " , (dele,seen) 
		else:
			print "error fetching all headers"

	print "\nyou have %d new messages\n" %(len(id_list))

def fetch_all_body():
	global id_list
	print "\n\n%%%%%%%%%%%%%%%%%%% Fetching all bodies\n"

	for num in reversed(id_list): # reverse order . latest first
		(flag,text_list) = fetch_email_body(num)
		if flag:
			print "\n============ body for message: %s " %(num)
			for i, text in enumerate(text_list):
				print "---- body part -----: ", i+1
				print text
			print "----------------------------------------------------\n"
		else:
			print "error fetching all body"


# if in main, not declared when called from hook
if __name__ == "__main__":

	m="melimelo5860"
	p="bastille5860"
	print "init imap: ", init_imap(m,p)
	print "list mailboxes: ",list_mailboxes()
	print "select INBOX: ",select_mailbox("INBOX")
	(flag,id_list)= search_mailbox()
	if not flag:
		print "error searching INBOX"
		sys.exit(1)
	else:
		print "search inbox: " , id_list

	while True:
		s  = raw_input("d delete, s search, h header, b body, p purge: ")

		if (str(s) == "d"):
			print "will set delete flag for latest ", id_list[-1]
			print set_delete_flag(id_list[-1])

		elif (str(s) == "s"):
			(flag,id_list)= search_mailbox()
			if not flag:
				print "error searching INBOX"
				sys.exit(1)
			else:
				print "search inbox: " , id_list

		elif (str(s) == "h"):
			fetch_all_headers()

		elif (str(s) == "b"):
			fetch_all_body()

		elif (str(s) == "p"):
			M.expunge()  

		else:
			exit_imap()	
			exit(0)

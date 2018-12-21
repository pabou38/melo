#!/usr/bin/python
# -*- coding: utf-8 -*-

# source file saved as utf 

#export PYTHONIOENCODING=utf8

#https://pabou.eu.ngrok.io        unvalid json
#https://pabou.eu.ngrok.io/test1  response as text
#https://pabou.eu.ngrok.io/test2  response as json

from __future__ import unicode_literals

# default text string are unicode u'\2655' legal
# s= u"this is a unicode string"
# it allows you in a Python 2 program to have the default interpretation of string literals be Unicode (UTF8). 


# https://stackoverflow.com/questions/38050182/how-to-generate-fixed-url-with-ngrok
# https://pabou38.serveo.net:443


#https://www.joelonsoftware.com/2003/10/08/the-absolute-minimum-every-software-developer-absolutely-positively-must-know-about-unicode-and-character-sets-no-excuses/
#unicodestring = u"Hello world"
# Convert Unicode to plain Python string: "encode"
# ie create a byte stream from a text string, using a given encoding 
#utf8string = unicodestring.encode("utf-8")
#asciistring = unicodestring.encode("ascii")

# Convert plain Python string to Unicode: "decode"
# ui create a text string by intepreting byte stream using a given encoding 
#plainstring1 = unicode(utf8string, "utf-8")
#plainstring2 = unicode(asciistring, "ascii")


# 23 juin 2017:  port to french
# 30 juin: add pense , clean analogie
# force gensim 2.2.0 pip install 'stevedore>=1.3.0,<1.4.0'
# 17 dec identification

from flask import Flask, request , render_template, make_response
from werkzeug import secure_filename
import json
import os
import argparse
import datetime
import sys

from OpenSSL import SSL
import logging
import subprocess

# subroutine to init, list, search, select , close
import re
from bs4 import BeautifulSoup
# pip install unidecode
#from unidecode import unidecode
import datetime
import signal
import thread #HL.  low level module is threading
import time
import pdb # pdbpp  to use old one pdb.pdb.set_trace()

# pabou
import yahoo
import mycrypto

server=Flask(__name__)


def sigterm_handler(a,b):
	print "got sigterm, close mailbox"
	logging.info(str(datetime.datetime.now())+ ' SIGTERM, close mailbox and exit process')
	try:
		yahoo.exit_imap()
	except Exception as e:
		print "exception in closing mailbox " + str(e)
	logging.error(str(datetime.datetime.now())+ ' exception in closing mailbox  ' + str(e))
	exit(0)	

def pico(text,lang):
	global pico_tell
	if pico_tell:
		# fr-FR  en-EN
		s="pico2wave -l " + lang + "  -w /home/pi/ramdisk/a.wav \"" + text +"\""
		print s
		os.system(s)
		#os.system("aplay -D plughw:0,0 /home/pi/ramdisk/a.wav >/dev/null 2>&1")
		os.system("aplay  /home/pi/ramdisk/a.wav >/dev/null 2>&1")
	else:
		pass

def ssml(text):
	speech = "<speak><audio src=\"https://actions.google.com/sounds/v1/alarms/beep_short.ogg\"/>"
	speech = speech + "<emphasis level=\"strong\">"
	speech = speech + text 
	speech = speech + "</emphasis>"
	speech = speech + "</speak>"
	return (speech)


def localization(lang):
	if lang == "en-us":
		return("list", "read", "bye", "again", "delete")
	else:
		return("liste", "lire", "bye" , "encore" , "efface"  )


# for dialogflow
#https://github.com/dialogflow/fulfillment-webhook-json/blob/master/responses/v2/response.json
def send_json_dialogflow(speech,text,cont):
        resp = {
        "fulfillmentText" : text,
        "fulfillmentMessages": [
        {
        "card": {
        "title": "melo meli",
        "subtitle": "Meaudre Robotics",
        "imageUri": "http://pabourudla.zapto.org/mots.jpg",
        "buttons": [
        {
        "text": "click for guide",
        "postback": "http://pabourudla.zapto.org/melo_meli.html"
        } ] } } ],
        "payload": {
        "google": {
        "expectUserResponse": cont,
        "richResponse": {
        "items": [
        {
        "simpleResponse": {
		"ssml": speech , "displayText": text }
			#"textToSpeech": text }
        } ]
        } } },
        "source" : "pabourudla.zapto.org/melo_meli.html"
        }
        return (resp)


#Simple responses can appear on audio-only, screen-only, or both surfaces. 
#They take the form of a chat bubble visually, and TTS/SSML sound
# actions.capability.AUDIO_OUTPUT and actions.capability.SCREEN_OUTPUT
def send_json_action_simple(speech, text, lang, cont):
	resp = {
	"payload": {
  	"google": {
      	"expectUserResponse": cont,
      	"richResponse": {
        "items": [
      	{
     		"simpleResponse": {
#      		"textToSpeech": speech ,
      		"ssml": speech ,
     		"displayText": text
    		}}]
  		}}}}
	return (resp)


#Rich responses can appear on screen-only or audio and screen experiences. They can contain the following components:
# One or two simple responses (chat bubbles)
# An optional basic card (image (192, url, centered),  title and sub title (one line, fixed font size),  
#       text body, link button (need link title), border (imageDisplayOptions JSON property, WHITE,DEFAULT,CROPPED))
# Optional suggestion chips (8 max, hint at response, not in FinalResponse)
# An optional link-out chip
#

#  option interface: Browsing carousel (link to web pages), list, carousel. cannot have basic card and optiuon interface at the same time
#  media response, table card, 

# Rich action response. need screen 
# Supported on actions.capability.SCREEN_OUTPUT surfaces.

# hook can use systemIntend to ask assistant to ask the user for options , ...
#     see https://developers.google.com/actions/build/json/dialogflow-webhook-json


def send_json_action_rich(speech,text,lang,cont):
	# cont expected user response True to continue
	(liste, lire, bye, encore, efface) = localization(lang) 
	#print "create %s json response %s %s %s" %(lang,liste,lire,bye)
	# this is a dict
	resp = {
  		"payload": {
    		"google": {
      		"expectUserResponse": cont,
#Indicates whether your fulfillment expects a user response. Set the value to true when to keep the conversation going and false to end the conversation.
# false, end conversation
		"richResponse": {
        	"items": 
		[
                 { "simpleResponse": { "ssml": speech,  "displayText": text } },
#The source url of the image. Images can be JPG, PNG and GIF (animated and non-animated).All images forced to be 192 dp tall.
#If the image's aspect ratio is different than the screen, the image is centered with gray bars on either vertical or horizontal edges.
		{ "basicCard": { "title": "Melo Meli v1.3", "image": {"url": "http://pabourudla.zapto.org/spooky.jpg", "accessibilityText": "Meaudre Robotics" } ,

		"buttons": [ { "title": "click for guide", "openUrlAction": { "url": "http://pabourudla.zapto.org/melo_meli.html" } } ]

		,
	              "imageDisplayOptions": "CROPPED"  # WHITE CROPPED DEFAULT
            	}
          	}
        	] 
		,
		"suggestions": [ { "title": liste }, { "title": lire }, { "title": bye } , {"title":encore}, {"title":efface}  ]

		}

# Rich response contains audio, text, cards, suggestions, or structured data for the Assistant to render. To learn more about using rich responses for Actions on Google, see Responses
		} } }

	#print resp
	# send json by returning
	return (resp)


# simple static text string
@server.route("/test", methods=['POST', 'GET'])
def handler_test():
	print "test flask handler, simple text string"
	resp = "melo meli is walking.  It's just a raspberry"
	r=make_response(resp)
	r.headers['Content-Type'] = 'text/plain'
	return (r) 


# id_list 1 to 5  index 0 to 4
# init to 0, first read will call next index and set to 4
def next_index(index):
	# index for next message . start from latest (highest num) , and decrement
	index=index-1
	if index==-1:
		index=len(id_list)-1
	print "next index_read %d: " %(index)
	return (index)

def prev_index(index):
	# index for previous message . start from latest (highest num)
	index=index+1
	if index==len(id_list):
		index=0
	print "prev index_read %d: " %(index)
	return (index)

# return ssml. end of each response
def footer(lang):
	s = "<emphasis level=\"strong\">" + \
		localization(lang)[0] + ". " + localization(lang)[1] + ". " + localization(lang)[2] + ". " + localization(lang)[3] + ". " + localization(lang)[4]\
		+"</emphasis>"
	return(s)

# call yahoo. fetch all headers and flag, and populate mail_header global dict
# OPTIMIZE ????? fetch range?  long operation will cause assistant timeout
# used as thread
def fetch_all_headers(p):
	global id_list # need to be set
	global mail_header # will populate
	global mail_header_ready

	print "\nTHREAD: %s  mail header dict: %r " %(p, bool(mail_header))

	# shared var to describe status not_ready, ready, failed
	mail_header_ready = not_ready

	logging.info(str(datetime.datetime.now())+ ' fetching headers. should be empty (false)' + str(bool(mail_header)) )

	for num in reversed(id_list): # start from latest OPTIMIZE ???? fetch range
		(flag, from_add, to_add, subject, (dele,seen)) = yahoo.fetch_email_headers(num)
		if not flag:
			print "THREAD: error fetching header"
			logging.error(str(datetime.datetime.now())+ ' ERROR fetching headers')
			flag = False
			mail_header_ready = failed
		else:
			# remove <> in address, mess with ssml
			from_add = re.sub(r'<.*>',"",from_add)
			to_add = re.sub(r'<.*>',"",to_add)
			# mail_header dict, key num , value  tuple from, subjet, (bol, bol). create once for all
			mail_header.update({num:(from_add,subject,(dele,seen))})
			flag = True
			mail_header_ready = ready

	print "THREAD: fetch mail headers returns: dict %r, flag %r, ready %d: " %( bool(mail_header) , flag , mail_header_ready)	
	#print mail_header
	#print id_list
	return (flag)
	# thread terminates when function returns
	# set mail_header_ready to ready or failed


##################################################
# INTEND handler
##################################################

def test_code(contentdict, lang):
	print contentdict['queryResult'] ['parameters']
	test = contentdict['queryResult'] ['parameters'] ['test']
	if lang == "en-us":
		return  ssml("you said %s" %(test))
	else:
		return ssml("vous avez dit %s" %(test))



def identification(contentdict,lang):
	global id_list
	global index_read
	global connected

	user=pin=cred=key=""
	# initial design , 3 entities, only one is set
	#for x in ["lili","pabou","melo"]:
	# 3 parameters, and none optional (cannot define a single entity). so all 3 could be empty


	# user pabou key word
	# user pabou key 1 2 3 4
	# either key or 3 or more number are set.
	# user entity with multiple entries

	print contentdict['queryResult'] ['parameters']

	for x in ["user"]:
		# this test if entry has key but no value.  exception if key does not exist. dialogflow must send all parameters (optional)
		if contentdict['queryResult'] ['parameters'] [x]:
			user = contentdict['queryResult'] ['parameters'] [x]
	"""
	not used anymore. key sys.any catches everything. so consider word or 1 2 3 as the same
	for x in ["number","number1","number2","number3","number4","number5"]:
		if contentdict['queryResult'] ['parameters'] [x] != u'': # have been filled. potentially xith float 0.0
			# numbers comes as float , convert to int, then to string , used by crypto
			pin = pin +  str(int(contentdict['queryResult'] ['parameters'] [x]))
	"""

	key = contentdict['queryResult'] ['parameters'] ['key']
	# not used. keyword is a plain sys.any
	#cred = contentdict['queryResult'] ['parameters'] ['cred']

	# give up for now on managing numeric pins. not worth the trouble. so cred not used really anymore. keep for future
	print "user is %s. key %s %d:" %(user,  key, len(key))
	logging.info(str(datetime.datetime.now())+ ' user %s. key %s' %(user,  key))

	if user == "":
		if lang == "en-us":
			return  ssml("did not catch user name")
		else:
			return ssml("je n'ai pas compris le nom de l'utilisateur")

	"""
	if cred in ["code","code"]:
		cred_i=key
	else:
		cred_i=key
	"""

	cred_i=key
	print "will use cred: %s" %( cred_i)

###################
# get password
	# return email address to be used for imap logging, and clear password
	(mail,pa) = mycrypto.decode(cred_i,user)
	print "cryto returned mail address %s. connecting to IMAP" %( mail)
	(flag1,data1) = yahoo.init_imap(mail,pa)
	del pa # delete password
# del password
#####################

	if not flag1:
		#[AUTHENTICATIONFAILED] LOGIN Invalid credentials
		print "error loging to IMAP!!!  ", data1
		# remove unspokable
		err=" ".join(data1.split(" ")[1:])
		logging.error(str(datetime.datetime.now())+ ' Error Connecting to IMAP' + data1)
		if lang == "en-us":
			return ssml("error while connecting to mailbox with %s. Check code or key. %s." %(cred_i,err ))
		else:
			return ssml("erreur pendant la connection a la boite mail avec %s. Verifiez le code ou la clef. %s." %(cred_i,err))

	else: # logging OK, can go to INBOX
		(flag2,data2)=yahoo.select_mailbox("INBOX")
		if not flag2:
			print "error selecting INBOX!!! ", data2
			logging.error(str(datetime.datetime.now())+ ' Error selecting INBOX' + data2)
			if lang == "en-us":
				return ssml("error while selecting INBOX. Quit app and retry")
			else:
				return ssml("erreur pendant la selection de INBOX. Quitter l'application et recommencez")

	# both calls to yahoo are OK
	print "IMAP init OK!!"
	connected=True
	logging.info(str(datetime.datetime.now())+ ' Connected to IMAP')
	# check data2 to see if any new message and avoid fetching headers
	#['4']
	# in fact data 2  is the  number of all messages, not only new (UNSEEN)
	print data2
	if int(data2[0]) == 0:
		if lang == "en-us":
			return ssml("No messages in INBOX. say quit")
		else:
			return ssml("pas de messages dans l'INBOX. dites au revoir")

	else: # need to search mailbox to get message list and then
		# get message list to announce. set global
		(flag,id_list) = yahoo.search_mailbox()

		if flag and id_list: # list messages OK , id_list not empty (ie new unseen messages)
			print "search OK, and list of UNSEEN message not empty"
			print "start thread for fetch all headers, while we speak how many messages"
			thread.start_new_thread( fetch_all_headers, ("from identification intent", ) )

			# speak number of messages
			msg_num = len(id_list)
			#  space between >< will show as space in text version
			speech = "<speak><audio src=\"https://actions.google.com/sounds/v1/cartoon/cartoon_boing.ogg\"/>"
			if lang == "en-us":
				speech = speech + "You have: "
			else:
				speech = speech + "Vous avez: "

			speech = speech + "<break time=\"500ms\"/>"
			speech  = speech + str(msg_num) + " messages\n\n" # new line ignored by ssml but formating for text version
			speech = speech + "<break time=\"1000ms\"/>"
			speech = speech + footer(lang)
			#speech = speech + "<emphasis level=\"strong\">List. Read. Bye</emphasis>"
			speech = speech + "</speak>"

			index_read=0 # next read will pick next first, and roll over to len(id_list)-1  Index vs id_list 
			print "set index_read to: ", index_read , id_list

			logging.info(str(datetime.datetime.now())+ ' %d new messages' %(len(id_list)))
			return(speech)

		elif not flag: # error fetch headers
			if lang == "en-us":
				return ssml("error while listing inbox")
			else:
				return ssml("error pendant la liste de l'inbox")
			logging.error(str(datetime.datetime.now())+ ' ERROR listing INBOX')
			print "ERROR listing INBOX"

		else: # id list empty
			print "id list empy, no new messages", id_list
			if lang == "en-us":
				return ssml("No new messages. say bye")
			else:
				return ssml("pas de nouveaux messages. dites bye")


##################################################
# flask handler
##################################################
#Your response must occur within 10 seconds, otherwise the Assistant assumes your fulfillment has timed out and ends your conversation.


@server.route("/", methods=['POST', 'GET'])
def handler():
	global screen
	speech = u" "
	# type unicode
	# declared as utf to mare sure. otherwise dictionary word with >128 will generate exception
	global mail_header # dict
	global mail_body # dict
	global id_list # list
	global index_read
	global screen_set
	global connected # connectec to IMAP

	intend = " "
	print "\n\n\n======== flask hander for / ========="
	start = datetime.datetime.now()
	logging.info(str(datetime.datetime.now())+ ' ----- > Flask handler started ')

	content = request.data
	req = request.get_json(silent=True, force=True)

	# how do I know it's comming from dialogflow (test or web tester)

	#print "-------------------------------------"
	#print json.dumps(req,indent=4)
	#print "-------------------------------------"

	lang=locale=""
	contentdict = json.loads(content)
	intend = contentdict['queryResult'] ['intent'] ['displayName']
	print intend
	lang = contentdict['queryResult'] ['languageCode']
	# en-us fr-fr
	print lang
	#locale = contentdict['originalDetectIntentRequest'] ['payload'] ['surface'] ['user'] ['locale']
	#print locale

	logging.info(str(datetime.datetime.now())+ ' ----- > received intend: %s. language code: %s, locale: %s' %( intend, lang, locale)  )

	pico("intend is: " + intend, "en-US")

	if not screen_set:  # set screen variable only at first interaction
		print "will figure out screen type"
		try:
			# this can trigger an exception. set screen variable
			# surface and available surface not the same json; available has one more list	
			available = contentdict['originalDetectIntentRequest'] ['payload'] ['surface'] ['capabilities']
			#capabilities = contentdict['originalDetectIntentRequest'] ['payload'] ['availableSurfaces']
			#available  = capabilities[0] ['capabilities']
			#list of dictionaries
			screen = False
			for c in available:
				cap = c['name']
  				#print cap
				if cap == "actions.capability.SCREEN_OUTPUT":
					screen = True
					print "SCREEN available"

		except:
			print "exception when getting surface. SCREEN not available"
			screen = False
			logging.error(str(datetime.datetime.now())+ ' Exception getting surface')
			# some param not availale when using dialog flow testing
	else:
		print "screen type already known"
		screen_set = True


	# is this comming from dialogflow or assistant
        try:
                source = contentdict['originalDetectIntentRequest'] ['source']
                print "request comming from assistant: ", source
                logging.info(str(datetime.datetime.now())+ ' from assistant %s' %(source))
                assistant = True
        except:
                print "exception. request comming from dialogflow web testing: "
                logging.info(str(datetime.datetime.now())+ ' from dialogflow')
                assistant = False


	speech=u" "

##################
# imap starts here
##################

# intend have a french and english version


#####################
#  test pin code entry
#####################

	if (intend in ["test_codef1"]):
		speech = test_code(contentdict,lang)

#####################
# identification
#####################

	# first to be called. does IMAP logging
	# two designs. énd one two stage dialog with followup and context
	elif (intend in ["identification" , "identification1f"]):
		speech = identification(contentdict,lang)


#####################
# list
#####################

	# same intend for both lang
	elif (intend in [ "list"]) and connected:

		print "processing: %s. mail header dict not empty: %r, mail header ready: %d" %( intend , bool(mail_header) , mail_header_ready )  

		# test if dich exist (possibly not filled ?
		if not bool(mail_header): # launch two ? normally should not happen as the thread has create the dict
			print "header dictionary does not exist, need to fetch"
			flag = fetch_all_headers()
		else:
			print "header dictionary already exist "
			# make sure to wait for thread to complete
			while mail_header_ready == not_ready:
				time.sleep(0.5) # add timeout infinite loop, or send signal to user!!
			# thread set mail_header_ready to ready or error values	
			print "thread is done reading headers" 

# !!!!! endless loop here. exit loop on fails not done, and flag = false not tested 

			if mail_header_ready == ready:
				flag = True
			else:
				flag = False # means failed

		if flag: # OK we got the headers 
			speech = "<speak><audio src=\"https://actions.google.com/sounds/v1/cartoon/cartoon_boing.ogg\"/>"

			for num in reversed(id_list):
				# num is a string, mail_header a dict, with num as key
				if mail_header[num][2][0]: # delete flag set
					speech = speech + "<audio src=\"https://actions.google.com/sounds/v1/alarms/winding_alarm_clock.ogg\"/>"
					print "message was marked deleted, do not list " , num
					#if lang == "en-us":
					#	speech = speech + "melo meli deleted this message\n" 		
					#else:
					#	speech = speech + "melo meli a efface ce message\n"		
					#speech = speech + "<break time=\"1500ms\"/>"

				else:
					speech = speech + "<s>"
					speech = speech + "From: %s\n" %(mail_header[num][0])
					speech = speech + "<break time=\"1000ms\"/>"
					speech = speech + "Subject: %s\n\n" % (mail_header[num][1])
					speech = speech + "</s>"
					speech = speech + "<break time=\"1500ms\"/>"

			# all header processed
			speech = speech +  footer(lang) 
			speech = speech + "</speak>"

		else: # fetched headers failed
			print "fetched all headers failed"
			logging.error(str(datetime.datetime.now())+ ' fetching all headers failed')
			if lang == "en-us":
				speech = ssml("error while getting messages headers")
			else:
				speech = ssml("erreur pendant l'acces aux entetes de messages")

#####################
# read
#####################

# move to next before read (ie go down index, from latest)
#index_read is global index , from len(id_list) to 1
# num same, string , jused for addressing in imaplib

	elif (intend in ["read",  "encore"] and connected):

		if not bool(mail_header):
			print "need to fetch headers"
			flag = fetch_header()
		else:
			print "fetched headers are already there"
			flag=True

		if flag: #  fetch header OK

			if intend in ["again1","encore"]:
				pass # read same message
			else:
				#read next message
				index_read = next_index(index_read)

			# read body from IMAP only if not fetched already
			# read only message. index_read
			num = id_list[index_read] # num is a string 
			print "index to be read %d, num %s" %(index_read, num)
			print mail_header[num]
			# check if message was delete
			if mail_header[num][2][0]:
				# message was flagged deleted
				print "message was deleted, do not render body ", num
				speech = "<speak>" # because I am using call to ssml
				speech = speech + "<audio src=\"https://actions.google.com/sounds/v1/alarms/winding_alarm_clock.ogg\"/>"
				if lang == "en-us":
					speech = speech + ssml("melo meli deleted this message. Hit read again\n") 		
				else:
					speech = speech + ssml("melo meli a efface ce message. Faire lecture de nouveau\n")		
				speech = speech + "<break time=\"1500ms\"/>"
				speech = speech + footer(lang) 
				speech = speech + "</speak>"

			else: # message not deleted, need to process

				if num not in mail_body: # body not fetched
					logging.info(str(datetime.datetime.now())+ ' fetching body for %d' %(index_read))
					print "\nbody not yet read, fetching and adding to body dictionary", num
					(flag, text_list) = yahoo.fetch_email_body(num)

					if not flag:
						print "error fetching body: ", num
						logging.error(str(datetime.datetime.now())+ ' ERROR fetching body for %d %s' %(index_read),num)
					else:
						mail_body.update({num:text_list}) # add to dict , text list is a list, of plain text or 'ignored subtype'
						#print "body dictionary (so far): ", mail_body # key num string, value list of string	
						# text list list of unicode string, either 'ignored something' or text
						#print (text_list)

				else: # body already fetched
					print "body already fetched"
					flag=True # we are ok


				# we tried to fetch body
				if flag: # body fetched OK , or already fetched, render body 
					print ("body fetch OK")
					speech = "<speak><audio src=\"https://actions.google.com/sounds/v1/cartoon/cartoon_boing.ogg\"/>"
					# num is a string
					speech = speech + "<p>"
					speech = speech + "From: %s\n" %(mail_header[num][0])
					speech = speech + "<break time=\"1000ms\"/>"
					speech = speech + "</p>"
					speech = speech + "<p>"
					speech = speech + "Subject: %s\n\n" % (mail_header[num][1])
					speech = speech + "<break time=\"1500ms\"/>"
					speech = speech + "</p>"

					# list non plain text body as ignored, at the end of the message ignored XXX
					ignored = [] # to add at the end

					for text in mail_body[num]: # text is payload.decode(utf)
						if text == "":
							pass
						elif text.split()[0] == "ignored":
							ignored.append(text.split()[1]) # will say at the end
						else:
							# real body
							speech = speech + "<p>"
							# do not show line text which start with >
							# also, do not send body more than 640 char. action limit + ergonomy
							# speech = speech + text
							buff = ""
							lines = text.split('\n')
							for line in lines:
								if len(line) == 0: # string index out of range
									pass
								elif line[0] == '>':
									pass
								else:
									if len(buff) < 1500:
										buff = buff + line + '\n'
									else:
										break
							speech = speech + buff

							#both speech and text are unicode
							#speech = speech + text.encode('utf-8')
							# u+2019 was not displayed correcly (rigth single quote in let's)
							speech = speech + "</p>"
							speech = speech + "\n"
							speech = speech + "<break time=\"2000ms\"/>"

					speech = speech + "<break time=\"2000ms\"/>"

					"""
					if ignored: # not empty list
						print "ignored: " , ignored
						#''.join(ignored) does not put space
						speech = speech + "\nNote: %s has ignored the following content: %s\n" %(my_name, ', '.join(ignored))
						speech = speech + "<break time=\"2000ms\"/>"
					"""

					# if flag.  other case are ssml sentences
					speech = speech + footer(lang) 
					speech = speech + "</speak>"

				else:  # flag false, error getting body , generate ssml error 
					print ("body fetch ERROR")
					if lang == "en-us":
						speech = ssml("error while getting message body")		
					else:
						speech = ssml("erreur pendant le telechargement du contenu du message")		
					speech = speech + "<speak>"
					speech = speech + footer(lang) 
					speech = speech + "</speak>"
			# message not deleted

		else:  # flag false, error getting headers
			if lang == "en-us":
				speech = ssml("error while getting message headers")		
			else:
				speech = ssml("erreur pendant le telechargement des entetes de message")		

			speech = speech + "<speak>"
			speech = speech + footer(lang) 
			speech = speech + "</speak>"

		# returned from read

	#elif (intend == "Default Welcome Intent"):

##########
# bye
##########

	# triggers on bye to close maibox
	elif (intend == "bye"):
		connected=False
		logging.info(str(datetime.datetime.now())+ ' bye: reset cache and exit')
		print "reset header and body cache, close mailbox"
		# reset all data structure, as daemon keeps running
		# empty dict are false  bool(dict)
		mail_body.clear()
		mail_header.clear()

		# dont go in IMAP if not connected. 
		if connected:
			try:
				yahoo.exit_imap()
			except Exception as e:
				print "exception in closing mailbox " + str(e)
				logging.error(str(datetime.datetime.now())+ ' exception in closing mailbox  ' + str(e))

		if lang == "en-us":
			speech = ssml("Be seeing you !!")
		else:
			speech = ssml("A plus dans le bus!!")


###########
#  delete
###########
	elif (intend in ["efface"] and connected): # global index_read is current message
		print "index read " , index_read, id_list
		print "deleting num: %s" %(id_list[index_read])
		#print mail_header[id_list[index_read]]
		try:
			# mark in IMAP as deleted
			s = yahoo.set_delete_flag(id_list[index_read])
		except Exception as e:
			print "delete email exception: " + str(e)
			logging.info(str(datetime.datetime.now())+ " delete exception %s " %(str(e))  )
			if lang == "en-us":
				speech = ssml("error while deleting email !!")
			else:
				speech = ssml("erreur pendant l'effacement de l'email !!")
		else:
			logging.info(str(datetime.datetime.now())+ " deleting %s , %s" %(id_list[index_read],s)  )
			if lang == "en-us":
				speech = ssml("delete is: %s" %(s[0]))
			else:
				speech = ssml("effacement est: %s" %(s[0]))		

			# set delete flag in body dictionary. used later to skip , etc ..			
			num = id_list[index_read]
			value = mail_header[num] # read dict entry
			print num, value

			# cannot update tuple. need to convert to list and back
			tup = value [2] # set delete flag to true in tuple
			tup = list(tup)
			tup[0]= True
			tup = tuple(tup)

			del mail_header[num] # delete and re create dir entry, just update tup
			mail_header.update({num:(value[0],value[1],tup)})

			value = mail_header[num] # read dict entry to check
			print num, value

###########
#  others
###########

	elif intend in [ "list", "efface", "read", "encore"] and not connected:
		if lang == "en-us":
			speech = ssml("Connect to email first")
		else:
			speech = ssml("Connectez vous d'abord")


	elif (intend == " "):
		# not a valid json ? someone
		logging.info(str(datetime.datetime.now())+ ' !!!! not a valid json request')
		speech = " "
		# still send ssml ? 

	else:
		logging.info(str(datetime.datetime.now())+ ' !!!! unknown intend: ' + intend)
		print "intend inconnu " , intend
		# bad intend or exception in decoding
		if lang == "en-us":
			speech = ssml("Minux does not understand what you want")
		else:
			speech = ssml("Minuxe ne comprends pas ce que tu veut")

		pico("je ne comprend pas ton intention  " ,"fr-FR")


#########
# send json response
#########

	# send webhook response
	# speech type str for door, read from file 
	# encode, otherwise encode error > 128 in ascii

	# plain text from sslm.  can use new line, ignored in ssml	

	#pdb.set_trace()

	text=BeautifulSoup(speech,features="html.parser").get_text()

	#Use unidecode - it even converts weird characters to ascii instantly, and even converts Chinese to phonetic ascii.
	#pip install unidecode
	# convert to ascii , BUT LOOSE SOME "...... " 
	#text = unidecode(text)
	#speech = unidecode(speech)

	text = text.encode('utf-8')
	speech = speech.encode('utf-8')

	# type str in P2 ??? should be unicode ??

	#####################
	#print "speech , text ",  type(speech) , type(text), len(speech) , len(text)
	#print speech
	#print text
	####################
	print "len speech %d, text %d: " %(len(speech), len(text))

	# continue dialog ?
	if intend == "bye":
		cont = False
	else:
		cont = True

	# from dialogflow test or web i/f or from action ?
	if assistant == False:
                print "send Dialogflow response"
                resp = send_json_dialogflow(speech, text, cont)
        else:
		if screen == True:
			print "ASSISTANT SCREEN: send rich response"
			resp=send_json_action_rich(speech,text,lang,cont)
		else:
			print "ASSISTANT NO SCREEN: send simple response"
			resp=send_json_action_simple(speech,text,lang,cont)

	# resp is a dict
	#print "json response: ", type(resp)

	###################
	#print resp
	###################

	logging.debug(str(datetime.datetime.now())+ ' speech response: ' + speech , len(speech))
	logging.info(str(datetime.datetime.now())+ ' plain text speech response: %d %s' %(len(text), text) ) 

	#wire = resp.encode('ascii', 'ignore') 

	resp = json.dumps(resp,indent=4)
	r=make_response(resp)
	r.headers['Content-Type'] = 'application/json'
	print "send json response: " , lang
	end = datetime.datetime.now()
	#print "START: " , start
	#print "END: " , end
	print "intend processing duration: ", end - start
	return (r)

########################  end of handler ##########################


################## 
# MAIN
################## 

#if __name__ == "__main__":

my_name = "melo meli"

error = False
screen_set=False # check and set capabilities only once. save time to avoid timeout

# dictionaries are used to cache.  cleared at logout, to make sure next session will have header and body synched
# dict.clear()   if bool(dict)

# read all header at once, and record in dict
mail_header = {} # global , key = num,  tuple

# fetch body as needed, record in dict
mail_body = {} # global , key = num,  value = list of text

id_list = [] # list of string. in sequence for non uid, unique but not in sequence for uid.  note 1 to n. index 0 tlo n-&
index_read=0 # index into id_list. initialized in init imap once id_list is read, so that 1st read will access latest message

# global var to share status of fetch_headers
ready=1
not_ready=-1
failed=0
mail_header_ready = not_ready

# connected to IMAP
connected=False

# pid file for monit
pid_file="/home/pi/ramdisk/hook_email.pid"
s = "sudo chmod 777 " + pid_file
os.system(s)

pid = str(os.getpid())
f = open(pid_file, 'w')
f.write(pid)
f.close()

# otherwise defauly text string is ascii
# and s = "fffff" + text string with accent generate an error 
reload(sys)
sys.setdefaultencoding('utf8')
print "python encoding %s " %(sys.getdefaultencoding())

pico_tell=False
print "pico is enabled ... " , pico_tell

# debug, info, warning, error, critical
log_file = "/home/pi/imap/log.log"
s = "sudo chmod 777 " + log_file
os.system(s)

print "set logging to:  " , log_file
logging.basicConfig(filename=log_file,level=logging.INFO)

logging.info(str(datetime.datetime.now())+ ' dialogflow V2 server starting ...' )
print "Dialogflow V2 API"

ap = argparse.ArgumentParser()
# positional (mandatory) argumant
# ap.add_argument("who", help="mandatory user name")
# --  optional  argument .   args is a dict
ap.add_argument("-s", "--https",  default="n", help="optional https y or n. default n (autoforwarding)")
args=vars(ap.parse_args()) # vars return dict attributes
secure = args["https"]
print "use of https?: ", secure
print "catch SIGTEM"
signal.signal(signal.SIGTERM, sigterm_handler)

print "to test ngrok https://email.eu.ngrok.io/test"

while True:
	try:
		print "------------- RUN FLASK API.AI WEB HOOK ---------------- "
		pico("Bon.  je me mets au boulot." ,  "fr-FR")
		if secure == "y":
			myport = 443
			print "\n==> flask will use https. expect certificates, bind on port " , myport
			s = "/home/pi/meaudreAI/ssl_certificate/sslforfree/"
			certif = s + "certificate.crt"
			key = s + "private.key"
			ca = s + "ca_bundle.crt"
			print "privatekey ", key
			logging.info(str(datetime.datetime.now())+ ' start Flask https')
			server.run(host="0.0.0.0", port=myport, ssl_context=(certif,key), debug=False )

		else: # use ngrok
			myport = 5001
			print "\n==> flask will use http.  bind on port " , myport
			logging.info(str(datetime.datetime.now())+ ' start Flask http')
			server.run(host="0.0.0.0", port=myport, debug=False )

	except KeyboardInterrupt:
		pico("Flask interruption clavier", "fr-FR")
		print "keyboard Interrupt"
		logging.info(str(datetime.datetime.now())+ ' Keyboard Interrupt. process will exit')
		break # while true

	except Exception as e:
		pico("Exception. Exception", "fr-FR")
		print "Exception in Main" , str(e) 
		logging.info(str(datetime.datetime.now())+ ' Exception in Main. exit ' + str(e))
		break # end less restart ? 
		#Exception in Main [Errno 32] Broken pipe

	finally:
		pico("Bon.  je vais me coucher.", "fr-FR")
		print "FLASK EXITING"
		logging.info(str(datetime.datetime.now())+ ' Flask is exiting')
		exit(0)

	# while true crlc not captures ? endless restart ?

print "close mailbox"
try:
	yahoo.exit_imap()
except Exception as e:
	print "exception in closing mailbox " + str(e)
logging.error(str(datetime.datetime.now())+ ' exception in closing mailbox  ' + str(e))

pico("Bon.  je vais me coucher.", "fr-FR")
print "FLASK EXITING"
logging.info(str(datetime.datetime.now())+ ' melo meli is exiting')
exit(0)

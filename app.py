# flask imports
from flask import Flask, request, redirect, url_for, flash, render_template, json, jsonify
from flask_heroku import Heroku

# Python library imports
import datetime
import oauth2 as oauth
import os
import pusher
import re
import requests
import time
from twilio.rest import TwilioRestClient
import twilio.twiml
import urllib

# Flask overhead
app = Flask(__name__)
heroku = Heroku(app)

# Pusher overhead
frontend = pusher.Pusher(app_id=os.environ['PUSHER_ID'],
	key=os.environ['PUSHER_KEY'], secret=os.environ['PUSHER_SECRET'])

# global vars
pending = {}

####################
# HELPER FUNCTIONS #
####################

# invokes an API call to Rdio, sent from client on payload
def rdio(payload):
	req = client.request('http://api.rdio.com/1/', 'POST', urllib.urlencode(payload))
	return req

def find_track(query):
	song_result = rdio({'method':'search', 'query':query, 'types':'Track', 'count':1})
	return json.loads(song_result[1])['result']['results'][0]

# helper method to send an SMS via Twilio
def send_text(to, body):
	twilio.sms.messages.create(to=to, from_=os.environ['TWILIO_NUMBER'], body=body)

def is_admin(person):
	return person[1:] == os.environ['TWILIO_ADMIN'][1:]

# returns a blank response to an API call
def blank_resp():
	resp = jsonify({})
	resp.status_code = 200
	return resp

#################
# API FUNCTIONS #
#################

# we need the currently playing song
def queue_song(person, query):
	# search Rdio for song
	p = re.compile(r'\s+by\s+', re.IGNORECASE)
	m = p.search(query)
	stripped_query = query
	if m:
		stripped_query = query[:m.start()] + ' ' + query[m.end():]
	song = find_track(stripped_query)
	if not is_admin(person):
		payment = charge_for_song(person, song['name'])
		if payment == -1: # Venmo account owner tried to queue a song as a non-admin. Edge case
			frontend['juke'].trigger('queue', {'song':song['key']})
			# text user confirmation
			send_text(person, song['name'] + ' by ' + song['artist'] + ' is queued, thank you!')
			return
		pending[payment] = { 'songkey' : song['key'], 
												 'songname': song['name'], 
												 'songartist': song['artist'], 
												 'person' : person
											 }
	else:
		frontend['juke'].trigger('queue', {'song':song['key']})
		# text user confirmation
		send_text(person, song['name'] + ' by ' + song['artist'] + ' is queued, thank you!')

def charge_for_song(person, song_name):
	ts = time.time()
	st = datetime.datetime.fromtimestamp(ts).strftime('%I:%M %p on %b %d, %Y')
	data = {
        "access_token":venmo_token,
        "phone":person,
        "note":"for playing " + song_name + " on Juke at " + st,
        "amount":-0.01
    }
	url = "https://api.venmo.com/payments"
	response = requests.post(url, data)
	response_dict = response.json()
	if 'id' not in response_dict:
		return -1
	return response_dict['id'] # store this in pending

def skip():
	frontend['juke'].trigger('skip')

#########
# VIEWS #
#########

# Asks for phone number input
@app.route('/', methods=['GET'])
def home():
	return render_template('admin.html')

# Shows the actual player
@app.route('/player', methods=['GET'])
def player():
	return render_template('index.html')

##############
# API ROUTES #
##############

# stores the admin phone number; invoked from '/'
@app.route('/admin_number', methods=['POST'])
def admin_number():
	print 'here'
	number = request.form['number']
	os.environ['TWILIO_ADMIN'] = number
	return redirect(url_for('player'))

# Venmo web-hook: user was confirmed to have paid for their song!
@app.route('/pay', methods=['POST'])
def pay():
	data = json.loads(request.data)['data']
	payment = data['id']
	status = data['status']
	if status == 'settled':
		person = pending[payment]['person']
		songkey = pending[payment]['songkey']
		songname = pending[payment]['songname']
		songartist = pending[payment]['songartist']
		frontend['juke'].trigger('queue', {'song':songkey})
		send_text(person, songname + ' by ' + songartist + ' is queued, thank you!')
		del pending[payment] # payment is settled
	elif status == 'cancelled':
		del pending[payment]

	return blank_resp()

# parses all possible Twilio responses and delegates as necessary
@app.route('/twilio', methods=['POST'])
def twilio():
	from_ = request.values.get('From', None)
	msg = request.values.get('Body', None)
	if msg.lower() == 'skip' and is_admin(from_):
		skip()
	elif msg.lower() == 'pause' and is_admin(from_):
		frontend['juke'].trigger('pause')
	elif msg.lower() == 'play' and is_admin(from_):
		frontend['juke'].trigger('play')
	# Web socket responds via '/current' API call
	elif msg.lower() == 'current':
		frontend['juke'].trigger('current', {'person':from_})
	# Web socket responds via '/next' API call
	elif msg.lower() == 'next':
		frontend['juke'].trigger('next', {'person':from_})
	# Admin skip. CURRENTLY UNIMPLEMENTED ON FRONT-END
	elif msg[0] == '*' and is_admin(from_):
		song = find_track(msg[1:])
		frontend['juke'].trigger('skip_to', {'song':song['key']}))
	else:
		queue_song(from_, msg)

	return blank_resp()

# Front-end response to user request for next song
@app.route('/current', methods=['POST'])
def current():
	person = request.values.get('person', None)
	song = request.values.get('song', None)
	artist = request.values.get('artist', None)
	send_text(person, 'Now playing: ' + song + ' by ' + artist)
	
	return blank_resp()

# Front-end response to user request for next song
@app.route('/next', methods=['POST'])
def next():
	person = request.values.get('person', None)
	song = request.values.get('song', None)
	artist = request.values.get('artist', None)
	if not song or not artist:
		send_text(person, 'No songs are currently queued.')
	else:
		send_text(person, 'Next up: ' + song + ' by ' + artist)
	
	return blank_resp()

####################
# USELESS OVERHEAD #
####################

# TODO: make use of api
# source: http://developer.rdio.com/docs/rest/oauth
def validate():
	# create the OAuth consumer credentials
	consumer = oauth.Consumer(os.environ['RDIO_KEY'], os.environ['RDIO_SECRET'])
	# make the initial request for the request token
	return oauth.Client(consumer)

def venmo():
	data = {
        "client_id":os.environ['VENMO_KEY'],
        "client_secret":os.environ['VENMO_SECRET'],
        "code":os.environ['VENMO_CODE']
        }
	url = "https://api.venmo.com/oauth/access_token"
	response = requests.post(url, data)
	response_dict = response.json()
	return response_dict.get('access_token')

client = validate()
venmo_token = os.environ['VENMO_TOKEN'] #venmo()
twilio = TwilioRestClient(os.environ['TWILIO_KEY'], os.environ['TWILIO_SECRET'])

# Flask overhead
if __name__ == '__main__':
	#playback_token = json.loads(rdio({'method':'getPlaybackToken', 'domain':'deejay-pennapps.herokuapp.com'})[1])['result']
	#print playback_token
	# create playlist if it does not already exist
	app.run(use_reloader=False, debug=True)


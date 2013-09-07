# flask imports
from flask import Flask, request, redirect, url_for, flash, render_template, json, jsonify, g
from flask_heroku import Heroku

# Python library imports
import oauth2 as oauth
import os
import pusher
from twilio.rest import TwilioRestClient
import twilio.twiml
import urllib

# Flask overhead
app = Flask(__name__)
heroku = Heroku(app)

# Pusher overhead
frontend = pusher.Pusher(app_id=os.environ['PUSHER_ID'],
	key=os.environ['PUSHER_KEY'], secret=os.environ['PUSHER_SECRET'])

####################
# HELPER FUNCTIONS #
####################

# invokes an API call to Rdio, sent from client on payload
def rdio(payload):
	req = client.request('http://api.rdio.com/1/', 'POST', urllib.urlencode(payload))
	return req

# helper method to send an SMS via Twilio
def send_text(to, body):
	twilio.sms.messages.create(to=to, from_=os.environ['TWILIO_NUMBER'], body=body)

#################
# SERVER ROUTES #
#################

@app.route('/', methods=['GET'])
def home():
	return render_template('index.html')

# we need the currently playing song
def queue_song(person, query):
	# search Rdio for song
	song_result = rdio({'method':'search', 'query':query, 'types':'Track', 'count':1})
	song = json.loads(song_result[1])['result']['results'][0]
	frontend['juke'].trigger('queue', {'song':song['key']})

	# text user confirmation
	send_text(person, song['name'] + ' is queued, thank you!')

def skip():
	frontend['juke'].trigger('skip')

# parses all possible Twilio responses and delegates as necessary
@app.route('/twilio', methods=['POST'])
def twilio():
	from_ = request.values.get('From', None)
	msg = request.values.get('Body', None)
	if msg.lower() == 'skip' and from_[1:] == os.environ['TWILIO_ADMIN'][1:]:
		skip()
	else:
		# right now, assuming all messages are the song name to play
		queue_song(from_, msg)
		# JUST FOR DEMO PURPOSES, AUTOMATICALLY SKIP
		skip()


	resp = jsonify({})
	resp.status_code = 200
	return resp

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

client = validate()
twilio = TwilioRestClient(os.environ['TWILIO_KEY'], os.environ['TWILIO_SECRET'])

# Flask overhead
if __name__ == '__main__':
	#playback_token = json.loads(rdio({'method':'getPlaybackToken', 'domain':'deejay-pennapps.herokuapp.com'})[1])['result']
	#print playback_token
	# create playlist if it does not already exist
	app.run(use_reloader=False, debug=True)


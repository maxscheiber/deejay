# flask imports
from flask import Flask, request, redirect, url_for, flash, render_template, json, jsonify, g
#from flask_heroku import Heroku

# Python library imports
import oauth2 as oauth
from twilio.rest import TwilioRestClient
import twilio.twiml
import urllib

# local imports
import config

# Flask overhead
app = Flask(__name__)
#heroku = Heroku(app)
add_cache = []

####################
# HELPER FUNCTIONS #
####################

# invokes an API call to Rdio, sent from client on payload
def rdio(payload):
	return client.request('http://api.rdio.com/1/', 'POST', urllib.urlencode(payload))

# helper method to send an SMS via Twilio
def send_text(to, body):
	twilio.sms.messages.create(to=to, from_=config.TWILIO_NUMBER, body=body)

#################
# SERVER ROUTES #
#################

@app.route('/', methods=['GET'])
def home():
	return render_template('index.html', playback_token=playback_token)

@app.route('/poll', methods=['GET'])
def poll():
	tmp = []
	for x in add_cache:
		tmp.append(x)
	add_cache[:] = []
	return json.dumps(tmp)
	#return tmp # will this automatically get jsonified

# we need the currently playing song
def queue_song(person, query):
	# search Rdio for song
	song_result = rdio({'method':'search', 'query':query, 'types':'Track', 'count':1})
	print query
	song = json.loads(song_result[1])['result']['results'][0]
	add_cache.append(song['key'])
	print add_cache

	# text user confirmation
	send_text(person, song['name'] + ' is queued, thank you!')

# parses all possible Twilio responses and delegates as necessary
@app.route('/twilio', methods=['POST'])
def twilio():
	from_ = request.values.get('From', None)
	msg = request.values.get('Body', None)

	# right now, assuming all messages are the song name to play
	queue_song(from_, msg)
	return

####################
# USELESS OVERHEAD #
####################

# TODO: make use of api
# source: http://developer.rdio.com/docs/rest/oauth
def validate():
	# create the OAuth consumer credentials
	consumer = oauth.Consumer(config.RDIO_KEY, config.RDIO_SECRET)
	# make the initial request for the request token
	client = oauth.Client(consumer)
	return client

# Flask overhead
if __name__ == '__main__':
	twilio = TwilioRestClient(config.TWILIO_KEY, config.TWILIO_SECRET)
	client = validate()
	playback_token = json.loads(rdio({'method':'getPlaybackToken', 'domain':'localhost'})[1])['result']
	# create playlist if it does not already exist
	app.run(use_reloader=False, debug=True)


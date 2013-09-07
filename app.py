# flask imports
from flask import Flask, request, redirect, url_for, flash, render_template, json, jsonify
from flask_heroku import Heroku

# Python library imports
import cgi
import oauth2 as oauth
from twilio.rest import TwilioRestClient
import twilio.twiml
import urllib

# local imports
import config

# Flask overhead
app = Flask(__name__)
heroku = Heroku(app)

####################
# HELPER FUNCTIONS #
####################

# invokes an API call to Rdio, sent from client on payload
def rdio(client, payload):
	return client.request('http://api.rdio.com/1/', 'POST', urllib.urlencode(payload))

# helper method to send an SMS via Twilio
def send_text(to, body):
	twilio.sms.messages.create(to=to, from_=config.TWILIO_NUMBER, body=body)

#################
# SERVER ROUTES #
#################

# we need the currently playing song
def queue_song(query, person, playlist):
	# search Rdio for song
	song_result = rdio(auth_client, {'method':'search', 'query':query, 'types':'Track', 'count':1})
	song = json.loads(song_result[1])['result']['results'][0]
	print song

	# add the song
	rdio(auth_client, {'method':'addToPlaylist', 'playlist':playlist, 'tracks':song['key']})

	# text user confirmation
	send_text(person, song['name'] + ' is queued, thank you!')

# parses all possible Twilio responses and delegates as necessary
@app.route('/twilio', methods=['POST'])
def twilio():
	from_ = request.values.get('From', None)
	msg = request.values.get('Body', None)

	# right now, assuming all messages are the song name to play
	queue_song(msg, from_, "p6014113")
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
	response, content = client.request('http://api.rdio.com/oauth/request_token', 'POST', urllib.urlencode({'oauth_callback':'oob'}))
	parsed_content = dict(cgi.parse_qsl(content))
	request_token = oauth.Token(parsed_content['oauth_token'], parsed_content['oauth_token_secret'])

	# ask the user to authorize this application
	print 'Authorize this application at: %s?oauth_token=%s' % (parsed_content['login_url'], parsed_content['oauth_token'])
	oauth_verifier = raw_input('Enter the PIN / OAuth verifier: ').strip()
	# associate the verifier with the request token
	request_token.set_verifier(oauth_verifier)

	# upgrade the request token to an access token
	client = oauth.Client(consumer, request_token)
	response, content = client.request('http://api.rdio.com/oauth/access_token', 'POST')
	parsed_content = dict(cgi.parse_qsl(content))
	access_token = oauth.Token(parsed_content['oauth_token'], parsed_content['oauth_token_secret'])
	auth_client = oauth.Client(consumer, access_token)
	return auth_client

# Flask overhead
if __name__ == '__main__':
	twilio = TwilioRestClient(config.TWILIO_KEY, config.TWILIO_SECRET)
	auth_client = validate()
	# create playlist if it does not already exist
	app.run(use_reloader=False, debug=True)
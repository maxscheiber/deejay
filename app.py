# flask imports
from flask import Flask, request, redirect, url_for, flash, render_template, json, jsonify

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

####################
# HELPER FUNCTIONS #
####################

# invokes an API call to Rdio, sent from client on payload
def api(client, payload):
	return client.request('http://api.rdio.com/1/', 'POST', urllib.urlencode(payload))

#################
# SERVER ROUTES #
#################

# parses all possible Twilio responses and delegates as necessary
@app.route('/twilio', methods=['POST'])
def twilio():
	return # NOTHING RIGHT NOW LOL

####################
# USELESS OVERHEAD #
####################

def send_text(to, body):
	twilio.sms.messages.create(to=to, from_=config.TWILIO_NUMBER, body=body)

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
	auth_client = oauth.Client(consumer, request_token)
	response, content = client.request('http://api.rdio.com/oauth/access_token', 'POST')
	parsed_content = dict(cgi.parse_qsl(content))
	access_token = oauth.Token(parsed_content['oauth_token'], parsed_content['oauth_token_secret'])
	user_client = oauth.Client(consumer, access_token)

# Flask overhead
if __name__ == '__main__':
	twilio = TwilioRestClient(config.TWILIO_KEY, config.TWILIO_SECRET)
	validate()
	app.run(use_reloader=False)
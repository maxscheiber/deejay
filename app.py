# flask imports
from flask import Flask, request, redirect, url_for, flash, render_template, json, jsonify
#from flask_heroku import Heroku

# Spotify imports
from spotify import ArtistBrowser, Link, Playlist, ToplistBrowser, SpotifyError
from spotify.manager import (
	SpotifySessionManager, SpotifyPlaylistManager, SpotifyContainerManager)

# Python library imports
import cmd
import logging
import os
import threading
import time
from twilio.rest import TwilioRestClient
import twilio.twiml

# local imports
import config

# Flask overhead
app = Flask(__name__)
#heroku = Heroku(app)

####################
# HELPER FUNCTIONS #
####################

# helper method to send an SMS via Twilio
def send_text(to, body):
	twilio.sms.messages.create(to=to, from_=config.TWILIO_NUMBER, body=body)

#################
# SERVER ROUTES #
#################

# parses all possible Twilio responses and delegates as necessary
@app.route('/twilio', methods=['POST'])
def twilio():
	from_ = request.values.get('From', None)
	msg = request.values.get('Body', None)
	return

###########
# SPOTIFY #
###########

class Deejay(SpotifySessionManager):
	queued = False
	playlist = 2
	track = 0
	appkey_file = os.path.join(os.path.dirname(__file__), 'spotify_appkey.key')

	def __init__(self, *a, **kw):
		SpotifySessionManager.__init__(self, *a, **kw)
		print "Logging in, please wait..."

	def logged_in(self, session, error):
		if error:
			print error
		else:
			print 'logged in'
		self.session = session

####################
# USELESS OVERHEAD #
####################

# TODO: make use of api
def login():
	import optparse
	op = optparse.OptionParser(version="%prog 0.1")
	op.add_option("-u", "--username", help="Spotify username")
	op.add_option("-p", "--password", help="Spotify password")
	op.add_option(
		"-v", "--verbose", help="Show debug information",
		dest="verbose", action="store_true")
	(options, args) = op.parse_args()
	if options.verbose:
		logging.basicConfig(level=logging.DEBUG)
	deejay = Deejay(options.username, options.password, True)
	deejay.connect()

	print deejay.session.display_name()
	return deejay

# Flask overhead
if __name__ == '__main__':
	twilio = TwilioRestClient(config.TWILIO_KEY, config.TWILIO_SECRET)
	deejay = login()
	app.run(use_reloader=False, debug=True)
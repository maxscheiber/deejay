#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cmd
import logging
import os
import threading
import time

from spotify import ArtistBrowser, Link, Playlist, ToplistBrowser, SpotifyError
from spotify.manager import (
    SpotifySessionManager, SpotifyPlaylistManager, SpotifyContainerManager)


class Jukebox(SpotifySessionManager):
    queued = False
    playlist = 2
    track = 0
    appkey_file = os.path.join(os.path.dirname(__file__), 'spotify_appkey.key')

    def __init__(self, *a, **kw):
        SpotifySessionManager.__init__(self, *a, **kw)
        self.ctr = None
        self.playing = False
        self._queue = []
        self.track_playing = None
        print "Logging in, please wait..."

    def logged_in(self, session, error):
        print 'logged in'

if __name__ == '__main__':
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
    session_m = Jukebox(options.username, options.password, True)
    session_m.connect()

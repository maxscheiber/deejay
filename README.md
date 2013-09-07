Juke
====

Juke is an SMS-controlled music player allowing for groups of people to queue songs, with central skip and pause control. This is useful for parties and pregames. It also has Venmo integration, allowing a bar or restaurant to use it as a profit-generating jukebox.

Commands
--------
* **search query** - queues the first result matching your search query. We recommend song and artist, like *Fade Into Darkness Avicii*
* **current** - gives you the name and artist of the current song (not yet implemented)
* **next** - gives you the name and artist of the next song in line (not yet implemented)
* **skip** (admin-only) - goes to the next queued track

Stack
-----
Flask back-end, talking to JavaScript via Pusher. Venmo for payments, Twilio for SMS integration, Rdio for music.

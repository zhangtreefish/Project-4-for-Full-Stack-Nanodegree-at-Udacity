#!/usr/bin/env python

import webapp2
from google.appengine.api import app_identity
from google.appengine.api import mail
from api import TictactoeApi

class SetAnnouncementHandler(webapp2.RequestHandler):
    def get(self):
        """Set Announcement in Memcache."""
        # use _cacheAnnouncement() to set announcement in Memcache
        TictactoeApi.getAnnouncement()

class SendConfirmationEmailHandler(webapp2.RequestHandler):
    def post(self):
        """Send email confirming Game creation."""
        mail.send_mail(
            'noreply@{}.appspotmail.com' .format(
                app_identity.get_application_id()),     # from
            self.request.get('email'),                  # to
            'You created a new tictactoe game!',        # subj
            'Hi, you have created a following '         # body
            'game:\r\n\r\n{}' .format(self.request.get(
                'gameInfo'))
        )

app = webapp2.WSGIApplication([
    ('/crons/set_announcement', SetAnnouncementHandler),
    ('/tasks/send_confirmation_email', SendConfirmationEmailHandler),
], debug=True)

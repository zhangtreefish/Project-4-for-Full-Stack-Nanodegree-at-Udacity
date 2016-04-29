import webapp2
from google.appengine.api import app_identity
from google.appengine.api import mail
from api import TictactoeApi


class SetAnnouncementHandler(webapp2.RequestHandler):
    def get(self):
        """Set Announcement in Memcache."""
        # use _cacheAnnouncement() to set announcement in Memcache
        TictactoeApi.getAnnouncement(self.request)


# class SetMoveReminderHandler(webapp2.RequestHandler):
#     def get(self):
#     """Set Move Reminder in Memcache."""
#         TictactoeApi.getMoveReminder()


# class SendConfirmationEmailHandler(webapp2.RequestHandler):
#     def post(self):
#         """Send email confirming Game creation."""
#         mail.send_mail(
#             'noreply@{}.appspotmail.com' .format(
#                 app_identity.get_application_id()),     # from
#             self.request.get('email'),                  # to
#             'You created a new tictactoe game!',        # subj
#             'Hi, you have created a following '         # body
#             'game:\r\n\r\n{}' .format(self.request.get(
#                 'gameInfo'))
#         )
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

class SendMoveInviteEmailHandler(webapp2.RequestHandler):
    def post(self):
        """
        Send email inviting the player of the turn to make a move if 5days
        has elapsed since the last move.
        """
        # print('self.request', self.request)
        TictactoeApi.getMoveReminders(self.request)


app = webapp2.WSGIApplication([
    ('/crons/set_announcement', SetAnnouncementHandler),
    ('/tasks/send_confirmation_email', SendConfirmationEmailHandler),
    ('/tasks/send_move_invite_email', SendMoveInviteEmailHandler)
], debug=True)

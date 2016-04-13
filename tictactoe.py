#!/usr/bin/env python


from google.appengine.api import memcache
from models import StringMessage
from models import BooleanMessage
from google.appengine.ext import db

from google.appengine.api import taskqueue
from settings import WEB_CLIENT_ID
import endpoints
import logging
from additions.utils import getUserId
from protorpc import messages, message_types, remote
from models import PlayerForm, PlayerMiniForm, Player, GameForm, Game, GameForms
from google.appengine.ext import ndb

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID

PLAYER_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    user_name=messages.StringField(1),
    email=messages.StringField(2))
GAME_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeGameKey=messages.StringField(1),
)
# GAME_GET_REQUEST = endpoints.ResourceContainer(
#     message_types.VoidMessage,
#     websafeGameKey=messages.StringField(1),
# )
MEMCACHE_ANNOUNCEMENTS_KEY = "Recent Announcements"
DEFAULTS = {
    "positionOneA": '',
    "positionOneB": '',
    "positionOneC": '',
    "positionTwoA": '',
    "positionTwoB": '',
    "positionTwoC": '',
    "positionThreeA": '',
    "positionThreeB": '',
    "positionThreeC": ''
}

@endpoints.api( name='tictactoe',
                version='v1',
                allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID],
                scopes=[EMAIL_SCOPE])
class TictactoeApi(remote.Service):
    """Tictactoe API v0.1"""

# - - - Player objects - - - - - - - - - - - - - - - - - - -

    def _copyPlayerToForm(self, player):
        """Copy relevant fields from player to PlayerForm."""
        pf = PlayerForm()
        # all_fields: Gets all field definition objects. Returns an iterator
        # over all values in arbitrary order.
        for field in pf.all_fields():
            if hasattr(player, field.name):
                setattr(pf, field.name, getattr(player, field.name))
        pf.check_initialized()
        return pf

    def _getProfileFromPlayer(self):
        """Return player Profile from datastore, creating new one if non-existent."""
        # If the incoming method has a valid auth or ID token, endpoints.get_current_user()
        # returns a User, otherwise it returns None.
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)
        player_key = ndb.Key(Player, user_id)
        player = player_key.get()
        if not player:
            player = Player(
                key = player_key,
                displayName = user.nickname(),
                mainEmail= user.email(),
                gamesInProgress = [],
                gamesCompleted = [],
                winsTotal = 0,
                gamesTotal = 0)
            player.put()
        return player

    def _doProfile(self, edit_request=None):
        """Get player Profile and return to player, possibly updating it first."""
        # get user Profile
        player = self._getProfileFromPlayer()

        # if saveProfile(), process user-modifiable fields
        if edit_request:
            for field in ['displayName']:
                if hasattr(edit_request, field):
                    val = getattr(edit_request, field)
                    if val:
                        setattr(player, field, str(val))
            player.put()

        # return ProfileForm
        return self._copyPlayerToForm(player)


    @endpoints.method(message_types.VoidMessage, PlayerForm,
            path='player', http_method='GET', name='getPlayer')
    def getPlayer(self, request):
        """Return current player profile."""
        return self._doProfile(True)


# TODO: not updating
    @endpoints.method(PlayerMiniForm, PlayerForm,
            path='edit_player', http_method='POST', name='editPlayer')
    def editPlayer(self, request):
        """Update displayName & profile of the current player"""
        logging.info('saving your profile')
        return self._doProfile(request)

    # @ndb.transactional(xg=True)  # is it needed with the ancestor declaration?
    @endpoints.method(message_types.VoidMessage, GameForm,
            path='create_game', http_method='POST', name='createGame')
    def createGame(self, request):
        """
        create a game, creator automatically becomes playerOne; update
        player profile
        """
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)
        p_key = ndb.Key(Player, user_id)
        player = p_key.get()
        # allocate new Game ID with Player key as parent
        # allocate_ids(size=None, max=None, parent=None, **ctx_options)
        # returns a tuple with (start, end) for the allocated range, inclusive.
        g_id = Game.allocate_ids(size=1, parent=p_key)[0]
        # make Game key from ID
        g_key = ndb.Key(Game, g_id, parent=p_key)
        # # update player
        # player.gamesInProgress.append(g_key)
        # player.put()
        data = {}  # is a dict
        data['key'] = g_key
        data['playerOneId'] = user_id

        # add default values for those missing (both data model & outbound Message)
        # for df in DEFAULTS:
        #     if data[df] is None:
        #         data[df] = DEFAULTS[df]
        #         setattr(request, df, DEFAULTS[df])

        data['gameOver'] = False
        # data['gameCancelled'] = False
        data['gameCurrentMove'] = 0

        Game(**data).put()


        taskqueue.add(params={'email': user.email(),
            'gameInfo': repr(request)},
            url='/tasks/send_confirmation_email'
        )
        game = g_key.get()

        # player.gamesTotal = player.gamesTotal + 1  # throws TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'

        # displayName = p_key.get().displayName
        gf = self._copyGameToForm(game)
        return gf


    @endpoints.method(GAME_GET_REQUEST, GameForm,
            path='join_game/{websafeGameKey}', http_method='POST', name='joinGame')
    def joinGame(self, request):
        """current player joins a game as playerTwo"""
        # get the specified game
        print '!!', request.websafeGameKey
        game = ndb.Key(urlsafe=request.websafeGameKey).get()
        if not game:
            raise endpoints.NotFoundException(
                'No game found with key: %s' % request.websafeGameKey)
        # get the authorized user id
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)
        # update the specified game
        game.playerTwoId = user_id
        game.put()
        return self._copyGameToForm(game)

    # def playGame:

    @endpoints.method(message_types.VoidMessage, GameForms,
            path='games', http_method='GET', name='getPlayerGames')
    def getPlayerGames(self, request):
        """
        This returns all of a User's active games, including those as playerOne
        AND as playerTwo.
        """
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)
        p_key = ndb.Key(Player, user_id)
        games = Game.query(ancestor=p_key).fetch()
        player_two_games = Game.query(Game.playerTwoId==user_id).fetch()
        if player_two_games:
            for game in player_two_games:
                if game not in games:
                    games.append(game)
        return GameForms(
            items=[self._copyGameToForm(game) for game in games])

    @endpoints.method(GAME_GET_REQUEST, BooleanMessage,
            path='cancel_game/{websafeGameKey}', http_method='POST',
            name='cancelGame')
    def cancelGame(self, request):
        """
        allows either player to cancel a game in progress, implemented by
        deleting the Game model itself
        """
        # get the game
        game_key = request.websafeGameKey
        game = ndb.Key(urlsafe=game_key).get()
        # check if the current player is in the game
        user = user = endpoints.get_current_user()
        user_id = getUserId(user)
        cancelled = False
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        elif user_id not in [game.playerOneId, game.playerTwoId]:
            raise endpoints.UnauthorizedException('Only players can cancel \
                games')
        else:
            # game_key.delete()
            cancelled = True
            db.delete(game_key)
        return BooleanMessage(data =cancelled)



    # def getPlayerRankings:
    #     """ each Player's name and the 'performance' indicator (eg. win/loss
    #      ratio)."""
    # def getGameHistory:
    #     """ a 'history' of the moves for each game"""
# - - - Conference objects - - - - - - - - - - - - - - - - -

    def _copyGameToForm(self, game):
        """Copy relevant fields from Game to GameForm."""
        gf = GameForm()
        for field in gf.all_fields():
            if hasattr(game, field.name):
                setattr(gf, field.name, getattr(game, field.name))
            elif field.name == "websafeKey":  # TODO
                setattr(gf, field.name, game.key.urlsafe())
        # if displayName:
        #     setattr(gf, 'playerOneName', displayName)
        gf.check_initialized()
        return gf

    @endpoints.method(GAME_GET_REQUEST, GameForm,
            path='game/{websafeGameKey}',
            http_method='GET', name='getGame')
    def getGame(self, request):
        """Return requested game (by websafeGameKey)."""
        # get Game object from request; bail if not found
        game = ndb.Key(urlsafe=request.websafeGameKey).get()
        if not game:
            raise endpoints.NotFoundException(
                'No game found with key: %s' % request.websafeGameKey)
        player = game.key.parent().get()
        logging.debug('player')
        logging.debug(player)
        # return ConferenceForm
        return self._copyGameToForm(game)


    # def _getQuery(self, request):
    #     """Return formatted query from the submitted filters."""
    #     q = Conference.query()
    #     inequality_filter, filters = self._formatFilters(request.filters)

    #     # If exists, sort on inequality filter first
    #     if not inequality_filter:
    #         q = q.order(Conference.name)
    #     else:
    #         q = q.order(ndb.GenericProperty(inequality_filter))
    #         q = q.order(Conference.name)

    #     for filtr in filters:
    #         if filtr["field"] in ["month", "maxAttendees"]:
    #             filtr["value"] = int(filtr["value"])
    #         formatted_query = ndb.query.FilterNode(filtr["field"], filtr["operator"], filtr["value"])
    #         q = q.filter(formatted_query)
    #     return q


    # def _formatFilters(self, filters):
    #     """Parse, check validity and format user-supplied filters."""
    #     formatted_filters = []
    #     inequality_field = None

    #     for f in filters:
    #         print 'f.all_fields()', f.all_fields()
    #         logging.debug('f.all_fields()')
    #         logging.debug(f.all_fields())
    #         filtr = {field.name: getattr(f, field.name) for field in f.all_fields()}

    #         try:
    #             filtr["field"] = FIELDS[filtr["field"]]
    #             filtr["operator"] = OPERATORS[filtr["operator"]]
    #         except KeyError:
    #             raise endpoints.BadRequestException("Filter contains invalid field or operator.")

    #         # Every operation except "=" is an inequality
    #         if filtr["operator"] != "=":
    #             # check if inequality operation has been used in previous filters
    #             # disallow the filter if inequality was performed on a different field before
    #             # track the field on which the inequality operation is performed
    #             if inequality_field and inequality_field != filtr["field"]:
    #                 raise endpoints.BadRequestException("Inequality filter is allowed on only one field.")
    #             else:
    #                 inequality_field = filtr["field"]

    #         formatted_filters.append(filtr)
    #     return (inequality_field, formatted_filters)

    # # - - - Registration - - - - - - - - - - - - - - - - - - - -

    # @ndb.transactional(xg=True)
    # def _conferenceRegistration(self, request, reg=True):
    #     """Register or unregister user for selected conference."""
    #     retval = None
    #     prof = self._getProfileFromUser() # get user Profile

    #     # check if conf exists given websafeConfKey
    #     # get conference; check that it exists
    #     wsck = request.websafeConferenceKey
    #     conf = ndb.Key(urlsafe=wsck).get()
    #     if not conf:
    #         raise endpoints.NotFoundException(
    #             'No conference found with key: %s' % wsck)

    #     # register
    #     if reg:
    #         # check if user already registered otherwise add
    #         if wsck in prof.conferenceKeysToAttend:
    #             raise ConflictException(
    #                 "You have already registered for this conference")

    #         # check if seats avail
    #         if conf.seatsAvailable <= 0:
    #             raise ConflictException(
    #                 "There are no seats available.")

    #         # register user, take away one seat
    #         prof.conferenceKeysToAttend.append(wsck)
    #         conf.seatsAvailable -= 1
    #         retval = True

    #     # unregister
    #     else:
    #         # check if user already registered
    #         if wsck in prof.conferenceKeysToAttend:

    #             # unregister user, add back one seat
    #             prof.conferenceKeysToAttend.remove(wsck)
    #             conf.seatsAvailable += 1
    #             retval = True
    #         else:
    #             retval = False

    #     # write things back to the datastore & return
    #     prof.put()
    #     conf.put()
    #     return BooleanMessage(data=retval)

    # @endpoints.method(CONF_GET_REQUEST, BooleanMessage,
    #         path='conference/{websafeConferenceKey}',
    #         http_method='POST', name='registerForConference')
    # def registerForConference(self, request):
    #     """Register user for selected conference."""
    #     return self._conferenceRegistration(request)

    # @endpoints.method(CONF_GET_REQUEST, BooleanMessage,
    #         path='conference/{websafeConferenceKey}',
    #         http_method='DELETE', name='unregisterFromConference')
    # def unregisterFromConference(self, request):
    #     """Unregister user for selected conference."""
    #     return self._conferenceRegistration(request,False)

    # @endpoints.method(message_types.VoidMessage, ConferenceForms,
    #         path='conferences/attending',
    #         http_method='GET', name='getConferencesToAttend')
    # def getConferencesToAttend(self, request):
    #     """Get list of conferences that user has registered for."""
    #     # TODO:
    #     # step 1: get user profile
    #     prof = self._getProfileFromUser()
    #     # step 2: get conferenceKeysToAttend from profile.
    #     keys =getattr(prof,'conferenceKeysToAttend')
    #     logging.debug('keys')

    #     # TODO
    #     # to make a ndb key from websafe key you can use:
    #     # ndb.Key(urlsafe=my_websafe_key_string)
    #     safe_keys=[]
    #     for key in keys:
    #         safe_keys.append(ndb.Key(urlsafe=key))
    #     # step 3: fetch conferences from datastore.
    #     # Use get_multi(array_of_keys) to fetch all keys at once.
    #     # Do not fetch them one by one!
    #     conferences = ndb.get_multi(safe_keys)
    #     # return set of ConferenceForm objects per Conference
    #     return ConferenceForms(items=[self._copyConferenceToForm(conf, "")\
    #      for conf in conferences]
    #     )

    # - - - Announcements - - - - - - - - - - - - - - - - - - - -
    @staticmethod
    def _cacheAnnouncement():
        """Create Announcement & assign to memcache; used by
        memcache cron job & putAnnouncement().
        """
        confs = Conference.query(ndb.AND(
            Conference.seatsAvailable <= 5,
            Conference.seatsAvailable > 0)
        ) # TODO:get or.fetch(projection=[Conference.name])
        if confs:
            # If there are almost sold out conferences,
            # format announcement and set it in memcache
            announcement = '%s %s' % (
                'Last chance to attend! The following conferences '
                'are nearly sold out:',
                ', '.join(conf.name for conf in confs))
            memcache.set(MEMCACHE_ANNOUNCEMENTS_KEY, announcement)
        else:
            # If there are no sold out conferences,
            # delete the memcache announcements entry
            announcement = ""
            memcache.delete(MEMCACHE_ANNOUNCEMENTS_KEY)

        return announcement


    @endpoints.method(message_types.VoidMessage, StringMessage,
            path='tictactoe/announcement/get',
            http_method='GET', name='getAnnouncement')
    def getAnnouncement(self, request):
        """Return Announcement from memcache."""
        # TODO 1
        # return an existing announcement from Memcache or an empty string.
        # announcement = self._cacheAnnouncement()
        self._cacheAnnouncement()
        announcement = memcache.get(MEMCACHE_ANNOUNCEMENTS_KEY)
        if not announcement:
            announcement = ""
        return StringMessage(data=announcement)


# registers API
api = endpoints.api_server([TictactoeApi])

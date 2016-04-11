#!/usr/bin/env python


from google.appengine.api import memcache
from models import StringMessage
from google.appengine.ext import db

from google.appengine.api import taskqueue
from settings import WEB_CLIENT_ID
import endpoints
import logging
from additions.utils import getUserId
from protorpc import messages, message_types, remote
from models import PlayerForm, PlayerMiniForm, Player, GameForm
from google.appengine.ext import ndb

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID

PLAYER_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    user_name=messages.StringField(1),
    email=messages.StringField(2))
PLAYER_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1),
)

MEMCACHE_ANNOUNCEMENTS_KEY = "Recent Announcements"


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
                winTotal = 0,
                gameTotal = 0)
            player.put()
        return player

    def _doProfile(self, save_request=None):
        """Get player Profile and return to player, possibly updating it first."""
        # get user Profile
        player = self._getProfileFromPlayer()

        # if saveProfile(), process user-modifiable fields
        if save_request:
            for field in ('displayName'):
                if hasattr(save_request, field):
                    val = getattr(save_request, field)
                    if val:
                        setattr(player, field, str(val))
            player.put()

        # return ProfileForm
        return self._copyPlayerToForm(player)


    @endpoints.method(message_types.VoidMessage, PlayerForm,
            path='player', http_method='GET', name='getPlayer')
    def getPlayer(self, request):
        """Return user profile."""
        return self._doProfile(True)


    @endpoints.method(PlayerMiniForm, PlayerForm,
            path='player', http_method='POST', name='savePlayer')
    def savePlayer(self, request):
        """Update & return player profile."""
        logging.info('saving your profile')
        return self._doProfile(request)

    @endpoints.method(message_types.VoidMessage, GameForm,
            path='new_game', http_method='POST', name='createGame')
    def createGame(self, request):
        """create a game, creator automatically becomes playerOne"""
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)
        gf = GameForm(
            playerOneId = user_id,
            gameOver = False)
        return gf

    # def playGame:

    # def getPlayerGames:
    #     """
    #     This returns all of a User's active games. You may want to modify the
    #     User and Game models to simplify this type of query. Hint: it might
    #     make sense for each game to be a descendant of a User.
    #     """
    # def cancelGame:
    #     """
    #     This endpoint allows users to cancel a game in progress.
    #     You could implement this by deleting the Game model itself,
    #     or add a Boolean field such as 'cancelled' to the model. Ensure that
    #     Users are not permitted to remove completed games.
    #     """

    # def getPlayerRankings:
    #     """ each Player's name and the 'performance' indicator (eg. win/loss
    #      ratio)."""
    # def getGameHistory:
    #     """ a 'history' of the moves for each game"""
# - - - Conference objects - - - - - - - - - - - - - - - - -

    # def _copyConferenceToForm(self, conf, displayName):
    #     """Copy relevant fields from Conference to ConferenceForm."""
    #     cf = ConferenceForm()
    #     for field in cf.all_fields():
    #         if hasattr(conf, field.name):
    #             # convert Date to date string; just copy others
    #             if field.name.endswith('Date'):
    #                 setattr(cf, field.name, str(getattr(conf, field.name)))
    #             else:
    #                 setattr(cf, field.name, getattr(conf, field.name))
    #         elif field.name == "websafeKey":
    #             setattr(cf, field.name, conf.key.urlsafe())
    #     if displayName:
    #         setattr(cf, 'organizerDisplayName', displayName)
    #     cf.check_initialized()
    #     return cf


    # def _createConferenceObject(self, request):
    #     """Create or update Conference object, returning ConferenceForm/request."""
    #     # preload necessary data items
    #     user = endpoints.get_current_user()
    #     if not user:
    #         raise endpoints.UnauthorizedException('Authorization required')
    #     user_id = getUserId(user)

    #     if not request.name:
    #         raise endpoints.BadRequestException("Conference 'name' field required")

    #     # copy ConferenceForm/ProtoRPC Message into dict
    #     data = {field.name: getattr(request, field.name) for field in request.all_fields()}
    #     del data['websafeKey']
    #     del data['organizerDisplayName']

    #     # add default values for those missing (both data model & outbound Message)
    #     for df in DEFAULTS:
    #         if data[df] in (None, []):
    #             data[df] = DEFAULTS[df]
    #             setattr(request, df, DEFAULTS[df])

    #     # convert dates from strings to Date objects; set month based on start_date
    #     if data['startDate']:
    #         logging.info('date')
    #         logging.info(data['startDate'])
    #         print 'date', data['startDate']
    #         # datetime.date(): Return date object (y,m,d) to comply with DateProperty.
    #         data['startDate'] = datetime.strptime(data['startDate'][:10], "%Y-%m-%d").date()
    #         data['month'] = data['startDate'].month
    #     else:
    #         data['month'] = 0
    #     if data['endDate']:
    #         data['endDate'] = datetime.strptime(data['endDate'][:10], "%Y-%m-%d").date()

    #     # set seatsAvailable to be same as maxAttendees on creation
    #     # both for data model & outbound Message
    #     if data["maxAttendees"] > 0:
    #         data["seatsAvailable"] = data["maxAttendees"]
    #         setattr(request, "seatsAvailable", data["maxAttendees"])

    #     # make Profile Key from user ID
    #     p_key = ndb.Key(Profile, user_id)
    #     # allocate new Conference ID with Profile key as parent
    #     # allocate_ids(size=None, max=None, parent=None, **ctx_options)
    #     # returns a tuple with (start, end) for the allocated range, inclusive.
    #     c_id = Conference.allocate_ids(size=1, parent=p_key)[0]
    #     # make Conference key from ID
    #     c_key = ndb.Key(Conference, c_id, parent=p_key)
    #     data['key'] = c_key
    #     data['organizerUserId'] = request.organizerUserId = user_id

    #     # create Conference & return (modified) ConferenceForm
    #     #  ** means that  kw is initialized to a new dictionary receiving any
    #     # excess keyword arguments
    #     Conference(**data).put()
    #     taskqueue.add(params={'email': user.email(),
    #         'conferenceInfo': repr(request)},
    #         url='/tasks/send_confirmation_email'
    #     )
    #     return request


    # @endpoints.method(ConferenceForm, ConferenceForm, path='conference',
    #         http_method='POST', name='createConference')
    # def createConference(self, request):
    #     """Create new conference."""
    #     return self._createConferenceObject(request)


    # @endpoints.method(ConferenceQueryForms, ConferenceForms,
    #             path='queryConferences',
    #             http_method='POST',
    #             name='queryConferences')
    # def queryConferences(self,request):
    #     """Query for conferences."""
    #     conferences = self._getQuery(request)

    #      # return individual ConferenceForm object per Conference
    #     return ConferenceForms(
    #         items=[self._copyConferenceToForm(conf, "") for conf in conferences]
    #     )

    # @endpoints.method(message_types.VoidMessage, ConferenceForms,
    #     path='getConferencesCreated',
    #     http_method='POST',
    #     name='getConferencesCreated')
    # def getConferencesCreated(self, request):
    #     """Return conferences created by the user."""
    #     # make sure user is authed
    #     user = endpoints.get_current_user()
    #     if not user:
    #         raise endpoints.UnauthorizedException('Authorization required')

    #     # make profile key
    #     p_key = ndb.Key(Profile, getUserId(user))
    #     # create ancestor query for this user
    #     conferences = Conference.query(ancestor=p_key).fetch()
    #     # get the user profile and display name
    #     prof = p_key.get()
    #     displayName = getattr(prof, 'displayName')
    #     # return set of ConferenceForm objects per Conference
    #     return ConferenceForms(
    #         items=[self._copyConferenceToForm(conf, displayName) for conf in conferences]
    #     )

    # @endpoints.method(CONF_GET_REQUEST, ConferenceForm,
    #         path='conference/{websafeConferenceKey}',
    #         http_method='GET', name='getConference')
    # def getConference(self, request):
    #     """Return requested conference (by websafeConferenceKey)."""
    #     # get Conference object from request; bail if not found
    #     conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
    #     if not conf:
    #         raise endpoints.NotFoundException(
    #             'No conference found with key: %s' % request.websafeConferenceKey)
    #     prof = conf.key.parent().get()
    #     logging.debug('prof')
    #     logging.debug(prof)
    #     # return ConferenceForm
    #     return self._copyConferenceToForm(conf, getattr(prof, 'displayName'))

    # @endpoints.method(message_types.VoidMessage, ConferenceForms,
    #     path='filterConferences',
    #     http_method='GET',
    #     name='filterConferences')
    # def filterConferences(self, request):
    #     """return conferences of certain properties values"""

    #     # create ancestor query for this user,.filter(ndb.query.FilterNode(field, operator, value)) \
    #     conferences = Conference.query().filter(Conference.city == 'London')\
    #                   .filter(Conference.topics=='Medical Innovations')\
    #                   .filter(Conference.maxAttendees>10)
    #     return ConferenceForms(
    #         items=[self._copyConferenceToForm(conf, "") for conf in conferences]
    #     )

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

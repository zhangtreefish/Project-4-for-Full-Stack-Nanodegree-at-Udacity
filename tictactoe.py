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
from models import PlayerForm, PlayerMiniForm, Player, ConflictException
from models import GameForm, Game, GameForms, Move, MoveForm, ConflictException
from models import PositionNumber, PlayerNumber
from google.appengine.ext import ndb

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID

# PLAYER_REQUEST = endpoints.ResourceContainer(
#     message_types.VoidMessage,
#     user_name=messages.StringField(1),
#     email=messages.StringField(2))
GAME_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeGameKey=messages.StringField(1),
)
GAME_MOVE_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeGameKey=messages.StringField(1),
    positionTaken=messages.EnumField(PositionNumber, 2)
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
    "positionThreeC": '',
    "gameCurrentMove": 0,
    "seatsAvailable": 2,
    "moveLogs": []
}


@endpoints.api(name='tictactoe',
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
        """
        Return player Profile from datastore, creating new one if
        non-existent.
        """
        # If the incoming method has a valid auth or ID token, endpoints.get_
        # current_user() returns a User, otherwise it returns None.
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)
        player_key = ndb.Key(Player, user_id)
        player = player_key.get()
        if not player:
            player = Player(
                key=player_key,
                displayName=user.nickname(),
                mainEmail=user.email(),
                gamesInProgress=[],
                gamesCompleted=[],
                winsTotal=0,
                gamesTotal=0)
            player.put()
        return player

    def _getIdFromPlayer(self):
        """
        Return player Id from datastore, creating new one if non-existent.
        """
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)
        return user_id

    def _doProfile(self, edit_request=None):
        """
        Get player Profile and return to player, possibly updating it first.
        """
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

    def _copyGameToForm(self, game):
        """Copy relevant fields from Game to GameForm."""
        gf = GameForm()
        for field in gf.all_fields():
            if hasattr(game, field.name):
                setattr(gf, field.name, getattr(game, field.name))
            elif field.name == "websafeKey":
                setattr(gf, field.name, game.key.urlsafe())
        # if displayName:
        #     setattr(gf, 'playerOneName', displayName)
        gf.check_initialized()
        return gf

    def _copyMoveToForm(self, move):
        """Copy relevant fields from Move to MoveForm."""
        mf = MoveForm()
        # all_fields: Gets all field definition objects. Returns an iterator
        # over all values in arbitrary order.
        for field in mf.all_fields():
            if hasattr(move, field.name):
                setattr(mf, field.name, getattr(move, field.name))
        mf.check_initialized()
        return mf

    @endpoints.method(message_types.VoidMessage, PlayerForm,
                      path='player',
                      http_method='GET',
                      name='getPlayer')
    def getPlayer(self, request):
        """Return current player profile."""
        return self._doProfile(True)

    @endpoints.method(PlayerMiniForm, PlayerForm,
                      path='edit_player',
                      http_method='POST',
                      name='editPlayer')
    def editPlayer(self, request):
        """Update displayName & profile of the current player"""
        logging.info('saving your profile')
        return self._doProfile(request)

    @endpoints.method(message_types.VoidMessage, GameForm,
                      path='create_game',
                      http_method='POST',
                      name='createGame')
    def createGame(self, request):
        """
        create a game
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
        data = {}  # is a dict
        data['key'] = g_key

        # add default values for the missing(data model & outbound Message)
        # for df in DEFAULTS:
        #     if data[df] is None:
        #         data[df] = DEFAULTS[df]
        #         setattr(request, df, DEFAULTS[df])

        data['gameOver'] = False
        # data['gameCancelled'] = False
        data['gameCurrentMove'] = 0
        data['seatsAvailable'] = 2
        data['moveLogs'] = []
        Game(**data).put()

        taskqueue.add(params={'email': user.email(),
                      'gameInfo': repr(request)},
                      url='/tasks/send_confirmation_email')
        game = g_key.get()
        print 'game', game
        gf = self._copyGameToForm(game)
        return gf

    @endpoints.method(GAME_GET_REQUEST, GameForm,
                      path='participate_game/{websafeGameKey}',
                      http_method='POST',
                      name='participateGame')
    def participateGame(self, request):
        """
        authorized player participates in a game, can not play against self
        """
        # get the specified game
        print '!!', request.websafeGameKey
        game_key = ndb.Key(urlsafe=request.websafeGameKey)
        game = game_key.get()
        if not game:
            raise endpoints.NotFoundException(
                'No game found with key: %s' % request.websafeGameKey)
        # get the authorized user id
        player = self._getProfileFromPlayer()
        # check if the player has already signed up
        if game_key.urlsafe() in player.gamesInProgress:
                raise ConflictException(
                    "You have already registered for this game")
        # update the specified game
        user_id = self._getIdFromPlayer()
        if game.playerOneId is None:
            game.playerOneId = player.key.urlsafe()
            player.gamesInProgress.append(game_key.urlsafe())
            game.seatsAvailable -= 1

        elif game.playerTwoId is None:
            game.playerTwoId = player.key.urlsafe()
            player.gamesInProgress.append(game_key.urlsafe())
            game.seatsAvailable -= 1

        else:
            raise endpoints.UnauthorizedException('Sorry, both spots taken!')
        game.put()
        player.put()

        return self._copyGameToForm(game)

    @endpoints.method(message_types.VoidMessage, GameForms,
                      path='games', http_method='GET', name='getPlayerGames')
    def getPlayerGames(self, request):
        """
        This returns all games a player has signed up for, either as playerOne
        or as playerTwo.
        """
        player = self._getProfileFromPlayer()
        g_one = Game.query(Game.playerOneId == player.key.urlsafe()).fetch()
        g_two = Game.query(Game.playerTwoId == player.key.urlsafe()).fetch()
        # if player_two_games:
        #     for game in player_two_games:
        #         if game not in games:
        #             games.append(game)
        games = list(g_one)
        games.extend(g for g in g_two if g not in g_one)
        return GameForms(
            items=[self._copyGameToForm(game) for game in games])

    @endpoints.method(GAME_GET_REQUEST, BooleanMessage,
                      path='delete_game/{websafeGameKey}',
                      http_method='DELETE',
                      name='deleteGame')
    def deleteGame(self, request):
        """
        allows either player to cancel a game in progress, implemented by
        deleting the Game model itself
        """
        # get the game
        game_key = request.websafeGameKey
        game = ndb.Key(urlsafe=game_key).get()
        # check if the current player is in the game
        user_id = self._getIdFromPlayer()
        cancelled = False
        if not user_id:
            raise endpoints.UnauthorizedException('Authorization required')
        elif user_id not in [game.playerOneId, game.playerTwoId]:
            raise endpoints.UnauthorizedException('Only players can cancel \
                games')
        else:
            db.delete(game_key)  # game_key.delete() does not work
        return BooleanMessage(data=cancelled)

    @endpoints.method(message_types.VoidMessage, BooleanMessage,
                      path='delete_all_games', http_method='DELETE',
                      name='deleteAllGames')
    def deleteAllGames(self, request):
        """
        deleting all Games created by current player
        """

        ndb.delete_multi(Game.query().fetch(keys_only=True))
        deleted = True
        return BooleanMessage(data=deleted)

        # def getPlayerRankings:
    #     """ each Player's name and the 'performance' indicator (eg. win/loss
    #      ratio)."""
    # def getGameHistory:
    #     """ a 'history' of the moves for each game"""
# - - - Conference objects - - - - - - - - - - - - - - - - -

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
        # return ConferenceForm
        return self._copyGameToForm(game)

    # # - - - Registration - - - - - - - - - - - - - - - - - - - -
    @ndb.transactional(xg=True)
    def _gameParticipation(self, request, reg=True):
        """Register or unregister player for a selected game."""
        retval = None
        player = self._getProfileFromPlayer()  # get user Profile

        # check if game exists given websafeConfKey
        g_key = request.websafeGameKey
        game = ndb.Key(urlsafe=g_key).get()
        if not game:
            raise endpoints.NotFoundException(
                'No game found with key: %s' % g_key)

        # register
        if reg:
            if game.seatsAvailable <= 0:  # check if seats avail
                raise ConflictException(
                    "There are no seats available.")
            else:
                # register user, take away one seat
                if game.seatsAvailable == 1:  #register user
                    game.playerTwoId = player.key.urlsafe()
                elif game.seatsAvailable == 2:
                    game.playerOneId = player.key.urlsafe()
                player.gamesInProgress.append(g_key)  # update player profile
                game.seatsAvailable -= 1  # take away 1 seat
                retval = True

        # unregister
        else:
            # check if user already registered
            if g_key in player.gamesInProgress:
                # cancel player, add back one seat
                player.gamesInProgress.remove(g_key)
                game.seatsAvailable += 1
                # update game's player status
                if player.key.urlsafe() == game.playerOneId:
                    game.playerOneId = None
                if player.key.urlsafe() == game.playerTwoId:
                    game.playerTwoId = None
                retval = True
            else:
                retval = False

        # write things back to the datastore & return
        player.put()
        game.put()
        return BooleanMessage(data=retval)

    @endpoints.method(GAME_GET_REQUEST, BooleanMessage,
                      path='game/{websafeGameKey}',
                      http_method='POST', name='joinGame')
    def joinGame(self, request):
        """Register player for a selected game; can play against self."""
        return self._gameParticipation(request)

    @endpoints.method(GAME_GET_REQUEST, BooleanMessage,
                      path='game/{websafeGameKey}',
                      http_method='DELETE', name='leaveGame')
    def leaveGame(self, request):
        """Cancel user for a selected game."""
        return self._gameParticipation(request, False)

    @endpoints.method(GAME_MOVE_REQUEST, GameForm,
                      path='make_move/{websafeGameKey}/{positionTaken}',
                      http_method='POST',
                      name='makeMove')
    def makeMove(self, request):
        """
        authorized player makes a move: create a move, update Game, and if
        completed update Player
        """
        g_key = ndb.Key(urlsafe=request.websafeGameKey)
        # create a move
        m_id = Move.allocate_ids(size=1, parent=g_key)[0]
        m_key = ndb.Key(Move, m_id, parent=g_key)
        print 'm_key', m_key.urlsafe()
        data = {}
        data['key'] = m_key
        game = g_key.get()
        game.gameCurrentMove += 1
        data['moveNumber'] = game.gameCurrentMove
        if game.gameCurrentMove%2 == 1:
            data['playerNumber'] = 'One'
        elif game.gameCurrentMove%2 == 0:
            data['playerNumber'] = 'Two'
        data['positionTaken'] = str(request.positionTaken)
        Move(**data).put()
        move = m_key.get()
        # setattr(move, 'moveNumber', getattr(game, 'gameCurrentMove'))
        # setattr(move, 'positionTaken', str(request.positionTaken))
        # if game.gameCurrentMove%2 == 1:
        #     setattr(move, 'playerNumber', 'One')
        # elif game.gameCurrentMove%2 == 0:
        #     setattr(move, 'playerNumber', 'Two')
        logging.debug('move_b')
        logging.debug(move)
        move.put()
        logging.debug('move_af')
        logging.debug(move)

        # Update rest of the Game besides gameCurrentMove
        # game.moveLogs.append(move)
        # gameOver = ndb.BooleanProperty()
        player = self._getProfileFromPlayer()
        setattr(game, str(request.positionTaken), getattr(player, 'displayName'))
        game.put()

        # update player
        # player.gamesInProgress.append(game)
        # TODO: if done: update Player and Game

        return self._copyGameToForm(game)

    @endpoints.method(message_types.VoidMessage, GameForms,
                      path='games_active',
                      http_method='GET', name='getActiveGames')
    def getActiveGames(self, request):
        """Get a list of games that the player has made moves in."""
        # get user profile
        player = self._getProfileFromPlayer()
        # get gamesInProgress from profile.
        keys = getattr(player, 'gamesInProgress')
        logging.debug('keys')
        if keys is None:
            raise endpoints.NotFoundException(
                'You have 0 gamesInProgress')
        else:
            safe_keys = []
            for key in keys:  # to make key from wsks:ndb.Key(urlsafe=wsks)
                safe_keys.append(ndb.Key(urlsafe=key))
            games = ndb.get_multi(safe_keys)  # to fetch all keys at once
            if games:
                return GameForms(
                    items=[self._copyGameToForm(game) for game in games])

    # - - - Announcements - - - - - - - - - - - - - - - - - - - -
    @staticmethod
    def _cacheAnnouncement():
        """Create Announcement & assign to memcache; used by
        memcache cron job & putAnnouncement().
        """
        games = Game.query(ndb.AND(
            Game.seatsAvailable == 1,
            Game.seatsAvailable == 2)
        )  # TODO:get or.fetch(projection=[Conference.name])
        if games:
            # If there are games ready for sign up,
            # format announcement and set it in memcache
            announcement = '%s %s' % (
                'Come play... The following games '
                'are ready for you to sign up',
                ', '.join(game.name for game in games))
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

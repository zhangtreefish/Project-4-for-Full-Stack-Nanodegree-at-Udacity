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
from models import Game, GameForm, GamesForm, ConflictException
from models import PlayerRankForm, PlayersRankForm
from models import PositionNumber, PlayerNumber, Move, MoveForm, MovesForm
from google.appengine.ext import ndb
import base64
from utils import get_by_urlsafe

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
GAME_DEFAULTS = {
    # "positionOneA": '',
    # "positionOneB": '',
    # "positionOneC": '',
    # "positionTwoA": '',
    # "positionTwoB": '',
    # "positionTwoC": '',
    # "positionThreeA": '',
    # "positionThreeB": '',
    # "positionThreeC": '',
    # "gameCurrentMove": 0,
    # "seatsAvailable": 2,
    # "gameOver": False,
    # "gameCurrentMove": 0,
    # "seatsAvailable": 2,
    "gameWinner": None
}


@endpoints.api(name='tictactoe',
               version='v1',
               allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID],
               scopes=[EMAIL_SCOPE])
class TictactoeApi(remote.Service):
    """Tictactoe API v0.1"""

# - - - Player objects - - - - - - - - - - - - - - - - - - -

    def _copyPlayerToRankForm(self, player):
        """Copy relevant fields from player to PlayerRankForm."""
        prf = PlayerRankForm()
        # all_fields: Gets all field definition objects. Returns an iterator
        # over all values in arbitrary order.
        setattr(prf, 'displayName', getattr(player, 'displayName'))
        gamesWon = set()
        for g in player.gamesCompleted:
            game = get_by_urlsafe(g, Game)

            print 'g', g
            if game and game.gameWinner==player.displayName:
                gamesWon.add(g)

        # gamesWon = [g if g.gameWinner==player.displayName for g in player.gamesInProgress]
        winsTotal = len(gamesWon)
        gamesTotal = len(player.gamesCompleted)
        percentage = None
        if gamesTotal!=0:
            percentage = '{:.2%}'.format(float(winsTotal)/float(gamesTotal))
            print 'percentage', percentage
        setattr(prf, 'winsTotal', winsTotal)
        setattr(prf, 'gamesTotal', gamesTotal)
        setattr(prf, 'percentage', percentage)
        prf.check_initialized()
        return prf

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
                gamesCompleted=[])
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

    def _isWon(self, game):
        """when the tic-tac-toe game comes to a winning connection"""
        return (game.position1A==game.position2B==game.position3C!=None or
            game.position1A==game.position2B==game.position3C!=None or
            game.position1A==game.position1B==game.position1C!=None or
            game.position2A==game.position2B==game.position2C!=None or
            game.position3A==game.position3B==game.position3C!=None or
            game.position1A==game.position2A==game.position3A!=None or
            game.position1B==game.position2B==game.position3B!=None or
            game.position1C==game.position2C==game.position3C!=None)

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
                'No game found with key: {}' .format(request.websafeGameKey))
        # get the authorized user id
        player = self._getProfileFromPlayer()
        if not player:
            raise endpoints.NotFoundException('No player found')
        # check if the player has already signed up
        else:
            if game_key.urlsafe() in player.gamesInProgress:
                raise ConflictException(
                    "You have already registered for this game")
            # update the specified game
            else:
                if game.playerOneId is None:
                    setattr(game, 'playerOneId', player.key.urlsafe())
                    player.gamesInProgress.append(game_key.urlsafe())
                    # player.gamesTotal += 1
                    game.seatsAvailable -= 1

                elif game.playerTwoId is None:
                    game.playerTwoId = player.key.urlsafe()
                    player.gamesInProgress.append(game_key.urlsafe())
                    # player.gamesTotal += 1
                    game.seatsAvailable -= 1

                else:
                    raise endpoints.UnauthorizedException('Sorry, both spots taken!')
                game.put()
                player.put()

        return self._copyGameToForm(game)

    @endpoints.method(message_types.VoidMessage, GamesForm,
                      path='games', http_method='GET', name='getPlayerGames')
    def getPlayerGames(self, request):
        """
        This returns all games a player has signed up for, either as playerOne
        or as playerTwo.
        """
        player = self._getProfileFromPlayer()
        # get games as either as playerOne or playerTwo
        g_one = Game.query(Game.playerOneId == player.key.urlsafe()).fetch()
        g_two = Game.query(Game.playerTwoId == player.key.urlsafe()).fetch()
        # combine the two lists
        games = list(g_one)
        games.extend(g for g in g_two if g not in g_one)
        # check and return games form
        if not games:
            raise endpoints.NotFoundException(
                'Not a single game has this player signed up')
        return GamesForm(
            items=[self._copyGameToForm(game) for game in games])

    @endpoints.method(message_types.VoidMessage, GamesForm,
                      path='all_games', http_method='GET', name='allGames')
    def allGames(self, request):
        """
        This returns all games ever created by anyone on this app.
        """
        games = Game.query().fetch()
        return GamesForm(
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
        elif game.gameOver==True:
            raise endpoints.UnauthorizedException('Can not cancel finished\
                games')
        else:
            db.delete(game_key)  # game_key.delete() does not work
        return BooleanMessage(data=cancelled)

    # @endpoints.method(message_types.VoidMessage, BooleanMessage,
    #                   path='delete_all_games', http_method='DELETE',
    #                   name='deleteAllGames')
    # def deleteAllGames(self, request):
    #     """
    #     deleting all Games created by current player, except those that are
    #     played.
    #     """
    #     #keys_only:All operations return keys instead of entities.
    #     # keys_non_active
    #     ndb.delete_multi(Game.query().fetch(keys_only=True))
    #     deleted = True
    #     return BooleanMessage(data=deleted)

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

    # @endpoints.method(GAME_GET_REQUEST, BooleanMessage,
    #                   path='game/{websafeGameKey}',
    #                   http_method='POST', name='joinGame')
    # def joinGame(self, request):
    #     """
    #     Register player for a selected game; can play against self-not
    #     recommended.
    #     """
    #     return self._gameParticipation(request)

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
        authenticated player makes a move, implemented by creating a move,
         updating Game and Player
        """
        g_key = ndb.Key(urlsafe=request.websafeGameKey)
        game = g_key.get()
        # for some keys the following catches a bad key error:
        # game = get_by_urlsafe(request.websafeGameKey, Game)
        # g_key = game.key
        # check if the game is already completed
        if game.gameWinner:
            raise endpoints.UnauthorizedException('This game is already won.')
        # create a move
        m_id = Move.allocate_ids(size=1, parent=g_key)[0]
        m_key = ndb.Key(Move, m_id, parent=g_key)
        print 'm_key', m_key.urlsafe()

        player = self._getProfileFromPlayer()
        if not player:
            raise endpoints.NotFoundException('no player found')
        # check if game is signed up by two players and by the current player
        if game.playerOneId is None or game.playerTwoId is None:
            raise endpoints.UnauthorizedException('Need 2 players to start')
        if player.key.urlsafe() not in [game.playerTwoId, game.playerOneId]:
            raise endpoints.UnauthorizedException('You did not sign up')

        # check if the player had played the last move
        elif player.displayName==game.lastPlayer!= None:
            raise endpoints.UnauthorizedException(
                "Player, it is your opponent's turn")
        else:
            data = {}
            data['key'] = m_key
            data['moveNumber'] = game.gameCurrentMove + 1
            data['playerNumber'] = player.key.urlsafe()
            data['positionTaken'] = str(request.positionTaken)
            Move(**data).put()
            move = m_key.get()

            # Update Game on the position affected by the move, as well as player
            game.gameCurrentMove += 1
            setattr(game, str(request.positionTaken), getattr(player,
                    'displayName'))
            setattr(game, 'lastPlayer', getattr(player,
                    'displayName'))
            if self._isWon(game):
                setattr(game, 'gameOver', True)
                setattr(game, 'gameWinner', getattr(player,
                    'displayName'))
                player.gamesInProgress.remove(g_key.urlsafe())
                player.gamesCompleted.append(g_key.urlsafe())
                # setattr(player, 'winsTotal', player.winsTotal+1)
            game.put()
            player.put()

        return self._copyGameToForm(game)

    @endpoints.method(message_types.VoidMessage, GamesForm,
                      path='games_active',
                      http_method='GET', name='getActiveGames')
    def getActiveGames(self, request):
        """
        Get a list of games that the player has made moves in AND that have
        not ended.
        """
        # get user profile
        player = self._getProfileFromPlayer()
        # get gamesInProgress from profile.
        keys = getattr(player, 'gamesInProgress')
        logging.debug('keys')
        print 'keys', keys
        if keys is None:
            raise endpoints.NotFoundException(
                'You have 0 gamesInProgress')
        else:
            safe_keys = []
            for key in keys:  # to make key from wsks:ndb.Key(urlsafe=wsks)
                safe_keys.append(ndb.Key(urlsafe=key))
            games = ndb.get_multi(safe_keys)  # to fetch all keys at once
            print 'games', games
            if not games:
                raise endpoints.NotFoundException('No games found')
            else:
                return GamesForm(
                    items=[self._copyGameToForm(game) for game in games if game
                    and game.gameOver is False])

    @endpoints.method(message_types.VoidMessage, PlayersRankForm,
        path='players_ranking', http_method='GET', name='playersRanking')
    def getPlayerRankings(self, request):
        """
        a list consisting of each Player's name and the winning percentage
        """
        players = Player.query().fetch()
        return PlayersRankForm(
            items=[self._copyPlayerToRankForm(p) for p in players])


    @endpoints.method(GAME_GET_REQUEST, MovesForm,
                      path='game_history/{websafeGameKey}',
                      http_method='GET', name='gameHistory')
    def getGameHistory(self, request):
        """ shows a list of all the moves for each game"""
        game = get_by_urlsafe(request.websafeGameKey, Game)
        game_key = game.key
        moves = Move.query(ancestor=game_key).fetch()
        if not moves:
            raise endpoints.NotFoundException('No moves found')
        else:
            return MovesForm(items=[self._copyMoveToForm(move) for move in moves])


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
            # If there are no available games,
            # delete the memcache announcements entry
            announcement = ""
            memcache.delete(MEMCACHE_ANNOUNCEMENTS_KEY)

        return announcement

    @endpoints.method(message_types.VoidMessage, StringMessage,
                      path='tictactoe/announcement/get',
                      http_method='GET', name='getAnnouncement')
    def getAnnouncement(self, request):
        """Return Announcement from memcache."""
        self._cacheAnnouncement()
        announcement = memcache.get(MEMCACHE_ANNOUNCEMENTS_KEY)
        if not announcement:
            announcement = ""
        return StringMessage(data=announcement)


# registers API
api = endpoints.api_server([TictactoeApi])

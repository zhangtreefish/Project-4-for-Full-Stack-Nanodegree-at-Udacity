from google.appengine.api import memcache
from models import StringMessage
from google.appengine.ext import db
from google.appengine.api import taskqueue
from settings import WEB_CLIENT_ID
import endpoints
import logging
from protorpc import messages, message_types, remote
from models import PlayerForm, Player, ConflictException
from models import Game, GameForm, GamesForm
from models import PlayersRankForm, BooleanMessage
from models import Move, MovesForm, PositionNumber
from google.appengine.ext import ndb
import pickle
# import numpy as np

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID

PLAYER_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    user_name=messages.StringField(1),
    email=messages.StringField(2))
PLAYER_MINI_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    player_name=messages.StringField(1))
GAME_CREATE_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    game_name=messages.StringField(1),  # give the game a name
    player_name=messages.StringField(2)
)
GAME_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeGameKey=messages.StringField(1),
)
GAME_JOIN_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    player_name=messages.StringField(1),
    websafeGameKey=messages.StringField(2))
GAME_MOVE_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeGameKey=messages.StringField(1),
    positionTaken=messages.IntegerField(2),
    player_name=messages.StringField(3)
)

MEMCACHE_ANNOUNCEMENTS_KEY = "Recent Announcements"
DEFAULTS = {
    "seatsAvailable": 2,
    "gameOver": False,
    "gameCurrentMove": 0,
    "name":''
}

@endpoints.api(name='tictactoe',
               version='v1',
               allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID],
               scopes=[EMAIL_SCOPE])
class TictactoeApi(remote.Service):
    """Tictactoe API v0.1"""

    @endpoints.method(request_message=PLAYER_REQUEST,
                      response_message=PlayerForm,
                      path='user',
                      name='create_player',
                      http_method='POST')
    def createPlayer(self, request):
        """
        Create a Player. Requires a unique username; (an authenticated Google
        user can create multiple Players as long as the entered user_name is
        unique.)

        """
        if Player.query(Player.displayName == request.user_name).get():
            raise endpoints.ConflictException(
                    'A Player with that name already exists!')
        player = Player(displayName=request.user_name, mainEmail=request.email)
        player.put()
        return player._copyPlayerToForm

    @endpoints.method(GAME_CREATE_REQUEST, GameForm,
                      path='create_game',
                      http_method='POST',
                      name='create_game')
    def createGame(self, request):
        """
        a player creates a game of a unique name
        """
        player= Player.query(Player.displayName==request.player_name).get()
        if not player:
            raise endpoints.NotFoundException(
                'No player found with name: {}' .format(request.player_name))
        elif Game.query(Game.name == request.game_name).get():
            raise endpoints.ConflictException(
                    'A Game with that name already exists!')
        else:
            # allocate new Game ID with Player key as parent
            # allocate_ids(size=None, max=None, parent=None, **ctx_options)
            # returns a tuple with (start, end) for the allocated range, inclusive.
            p_key = player.key
            g_id = Game.allocate_ids(size=1, parent=p_key)[0]
            # make Game key from ID; assign initial values to the game entity
            g_key = ndb.Key(Game, g_id, parent=p_key)
            data = {}  # is a dict
            data['key'] = g_key
            data['name'] = request.game_name
            data['board'] = ['' for _ in range(9)]
            Game(**data).put()

            taskqueue.add(params={'email': player.mainEmail,
                          'gameInfo': repr(request)},
                          url='/tasks/send_confirmation_email')
            game = g_key.get()
            return game._copyGameToForm

    @endpoints.method(message_types.VoidMessage, GamesForm,
                      path='all_games', http_method='GET', name='all_games')
    def allGames(self, request):
        """
        This returns all games ever created by anyone on this app, sorted by
        seatsAvailable.
        """
        games = Game.query().fetch()
        items=[game._copyGameToForm for game in games]
        # sort by
        sorted_items = sorted(items, key=lambda gf: gf.seatsAvailable, reverse=True)
        return GamesForm(items=sorted_items)

    @endpoints.method(GAME_JOIN_REQUEST, GameForm,
                      path='participate_game/{websafeGameKey}',
                      http_method='POST',
                      name='participate_game')
    def participateGame(self, request):
        """
        Sign a player(identifiable by player_name) up for a game (identifiable
        by key); can not play against self
        """
        # get the specified game
        game_key = ndb.Key(urlsafe=request.websafeGameKey)
        game = game_key.get()
        if not game:
            raise endpoints.NotFoundException(
                'No game found with key: {}' .format(request.websafeGameKey))
        # get the requested player
        player = Player.query(Player.displayName==request.player_name).get()
        if not player:
            raise endpoints.NotFoundException(
                'No player with name {} found' .format(request.player_name))
        # check if the player has already signed up
        else:
            if game_key.urlsafe() in player.gamesInProgress:
                raise ConflictException(
                    "You have already registered for this game")
            # update the specified game
            else:
                if game.playerOne is None:
                    setattr(game, 'playerOne', request.player_name)
                    player.gamesInProgress.append(game_key.urlsafe())
                    game.seatsAvailable -= 1

                elif game.playerTwo is None:
                    game.playerTwo = request.player_name
                    player.gamesInProgress.append(game_key.urlsafe())
                    game.seatsAvailable -= 1

                else:
                    raise endpoints.UnauthorizedException('Sorry, both spots taken!')
                game.put()
                player.put()

        return game._copyGameToForm

    @endpoints.method(GAME_GET_REQUEST, GameForm,
                      path='game/{websafeGameKey}',
                      http_method='GET', name='get_game')
    def getGame(self, request):
        """Return requested game (by websafeGameKey)."""
        # get Game object from request; bail if not found
        game = ndb.Key(urlsafe=request.websafeGameKey).get()
        if not game:
            raise endpoints.NotFoundException(
                'No game found with key: {}' .format(request.websafeGameKey))
        # return GameForm
        return game._copyGameToForm


    @endpoints.method(GAME_JOIN_REQUEST, GameForm,
                      path='cancel_game/{websafeGameKey}',
                      http_method='DELETE', name='cancel_game')
    def cancelGame(self, request):
        """
        Cancels a user from a game if the game is not complete AND no player
        has ever made a first move.
        """
        g_key = ndb.Key(urlsafe=request.websafeGameKey)
        game = g_key.get()
        player = Player.query(Player.displayName==request.player_name).get()
        if player is None:
            raise endpoints.NotFoundException(
                'No player found with name: {}' .format(request.player_name))
        elif game is None:
            raise endpoints.NotFoundException(
                'No game found with key: {}' % request.player_name)
        elif g_key.urlsafe() in player.gamesCompleted:
            raise endpoints.UnauthorizedException(
                'Player can not cancel completed games')
        elif game.gameCurrentMove>0:
            raise endpoints.UnauthorizedException(
                'Players can not cancel once the first has been made')
        elif g_key.urlsafe() in player.gamesInProgress:
            # cancel player, add back one seat
            player.gamesInProgress.remove(g_key.urlsafe())
            game.seatsAvailable += 1
            # update game's player status
            if player.displayName == game.playerOne:
                game.playerOne = None
            if player.displayName == game.playerTwo:
                game.playerTwo = None
        else:
            raise endpoints.NotFoundException(
                'Player {} is not signed up with game {}' .format(
                    request.player_name, request.websafeGameKey))

        # write things back to the datastore & return
        player.put()
        game.put()
        return game._copyGameToForm

    @endpoints.method(PLAYER_MINI_REQUEST, GamesForm,
                      path='games', http_method='GET', name='get_user_games')
    def getPlayerGames(self, request):
        """
        This returns all games a player has signed up for but has not
        completed, i.e., those in the gamesInProgress list.
        """
        player = Player.query(Player.displayName==request.player_name).get()
        game_keys =getattr(player,'gamesInProgress')

        key_objects=[ndb.Key(urlsafe=key) for key in game_keys]

        # Use get_multi(array_of_keys) to fetch all games at once.
        games = ndb.get_multi(key_objects)

        if not games:
            raise endpoints.NotFoundException(
                'Not a single game has this player {} signed up for' .format(
                request.player_name))
        return GamesForm(
            items=[game._copyGameToForm for game in games if game])

    @endpoints.method(GAME_MOVE_REQUEST, GameForm,
                      path='make_move/{websafeGameKey}/{positionTaken}',
                      http_method='POST',
                      name='make_move')
    def makeMove(self, request):
        """
        authenticated player makes a move, implemented by creating a move,
         updating Game and Player
        """
        g_key = ndb.Key(urlsafe=request.websafeGameKey)
        game = g_key.get()

        # create a move
        m_id = Move.allocate_ids(size=1, parent=g_key)[0]
        m_key = ndb.Key(Move, m_id, parent=g_key)

        player = Player.query(Player.displayName==request.player_name).get()

        if game.gameWinner:
            raise endpoints.UnauthorizedException('This game is already won.')
        # check if game is signed up by two players and by the current player
        elif game.playerOne is None or game.playerTwo is None:
            raise endpoints.UnauthorizedException(
                'Need 2 signed-up players to start')
        elif not player:
            raise endpoints.NotFoundException('no player found')
               # check if the game is already completed
        elif player.displayName not in [game.playerTwo, game.playerOne]:
            raise endpoints.UnauthorizedException('You did not sign up')
        # check if the player had played the last move
        elif player.displayName==game.lastPlayer!= None:
            raise endpoints.UnauthorizedException(
                "Player {}, it is your opponent {}'s turn" .format(
                    game.playerOne, game.playerTwo))
        elif game.board[request.positionTaken]!='':
            raise endpoints.UnauthorizedException('The game board position {} \
             is already taken' .format(request.positionTaken))
        else:
            data = {}
            data['key'] = m_key
            data['moveNumber'] = game.gameCurrentMove + 1
            data['playerName'] = player.displayName
            data['positionTaken'] = request.positionTaken
            Move(**data).put()
            move = m_key.get()

            # Update Game on the position affected by the move, as well as player
            game.gameCurrentMove += 1
            game.board[request.positionTaken] = request.player_name
            setattr(game, 'lastPlayer', getattr(player,
                    'displayName'))
            if game._isWon:
                setattr(game, 'gameOver', True)
                setattr(game, 'gameWinner', getattr(player,
                    'displayName'))
                player.gamesInProgress.remove(g_key.urlsafe())
                player.gamesCompleted.append(g_key.urlsafe())
                # setattr(player, 'winsTotal', player.winsTotal+1)
            game.put()
            player.put()

        return game._copyGameToForm


    @endpoints.method(message_types.VoidMessage, BooleanMessage,
                      path='delete_all_games', http_method='POST',
                      name='delete_all_games')
    def deleteAllGames(self, request):
        """
        deleting all Games created by current player, except those that are
        played.
        """
        #keys_only:All operations return keys instead of entities.
        ndb.delete_multi(Game.query().fetch(keys_only=True))
        deleted = True
        return BooleanMessage(data=deleted)


    @endpoints.method(message_types.VoidMessage, PlayersRankForm,
        path='players_ranking', http_method='GET', name='get_user_rankings')
    def getPlayerRankings(self, request):
        """
        a list consisting of each Player's name and the winning percentage
        """
        players = Player.query().fetch()
        items=[p._copyPlayerToRankForm for p in players]
        sorted_items = sorted(items, key=lambda prf: prf.percentage, reverse=True)
        return PlayersRankForm(items=sorted_items)


    @endpoints.method(GAME_GET_REQUEST, MovesForm,
                      path='game_history/{websafeGameKey}',
                      http_method='GET', name='get_game_history')
    def getGameHistory(self, request):
        """ shows a list of all the moves for each game"""
        game_key = ndb.Key(urlsafe=request.websafeGameKey)
        moves = Move.query(ancestor=game_key).fetch()
        if not moves:
            raise endpoints.NotFoundException('No moves found')
        else:
            return MovesForm(items=[move._copyMoveToForm for move in moves])


    # - - - Announcements - - - - - - - - - - - - - - - - - - - -
    @staticmethod
    def _cacheAnnouncement():
        """Create Announcement & assign to memcache; used by
        memcache cron job & putAnnouncement().
        """
        games = Game.query(Game.seatsAvailable != 0).fetch()
        if games:
            # If there are games ready for sign up,
            # format announcement and set it in memcache
            announcement = '{} {}' .format(
                'Come play...The following games need more player!',
                ', '.join(game.name or '' for game in games))
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

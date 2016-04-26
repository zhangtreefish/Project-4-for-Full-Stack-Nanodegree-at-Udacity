import httplib
import endpoints
from protorpc import messages
from google.appengine.ext import ndb


class ConflictException(endpoints.ServiceException):
    """ConflictException -- exception mapped to HTTP 409 response"""
    http_status = httplib.CONFLICT


class Player(ndb.Model):
    """A Kind to represent player profile"""
    displayName = ndb.StringProperty()
    mainEmail = ndb.StringProperty()
    gamesInProgress = ndb.StringProperty(repeated=True)  # games signed up for
    gamesCompleted = ndb.StringProperty(repeated=True)

    @property
    def _copyPlayerToForm(self):
        """Copy relevant fields from player to PlayerForm."""
        pf = PlayerForm()
        # all_fields: Gets all field definition objects. Returns an iterator
        # over all values in arbitrary order.
        for field in pf.all_fields():
            if hasattr(self, field.name):
                setattr(pf, field.name, getattr(self, field.name))
        pf.check_initialized()
        return pf

    @property
    def _copyPlayerToRankForm(self):
        """Copy relevant fields from player to PlayerRankForm."""
        prf = PlayerRankForm()

        setattr(prf, 'displayName', getattr(self, 'displayName'))
        setattr(prf, 'mainEmail', getattr(self, 'mainEmail'))
        gamesWon = set()
        for g in self.gamesCompleted:
            game = ndb.Key(urlsafe=g).get()
            if game and game.gameWinner == self.displayName:
                gamesWon.add(g)

        winsTotal = len(gamesWon)
        gamesTotal = len(self.gamesCompleted)
        percentage = 0.00
        # rounded_pct = 0
        if gamesTotal != 0:
            # percentage = '{:.2%}'.format(float(winsTotal)/float(gamesTotal))
            percentage = float(winsTotal)/float(gamesTotal)
            # rounded_pct = int(np.round(percentage/0.01))*0.01
        setattr(prf, 'winsTotal', winsTotal)
        setattr(prf, 'gamesTotal', gamesTotal)
        setattr(prf, 'percentage', percentage)
        prf.check_initialized()
        return prf


class Game(ndb.Model):
    """A Kind for Game, instantiate with Player as parent"""
    name = ndb.StringProperty()
    seatsAvailable = ndb.IntegerProperty(default=2)
    playerOne = ndb.StringProperty()
    playerTwo = ndb.StringProperty()
    board = ndb.PickleProperty()
    # moveLogs = ndb.StructuredProperty(Move, repeated=True)
    gameCurrentMove = ndb.IntegerProperty(default=0)
    lastPlayer = ndb.StringProperty()
    gameOver = ndb.BooleanProperty(default=False)
    gameWinner = ndb.StringProperty()

    @property
    def _copyGameToForm(self):
        """Copy relevant fields from Game to GameForm."""
        gf = GameForm()
        for field in gf.all_fields():
            if hasattr(self, field.name):
                setattr(gf, field.name, getattr(self, field.name))
            elif field.name == "websafeKey":
                setattr(gf, field.name, self.key.urlsafe())
            elif field.name == "gameBoard":
                setattr(gf, field.name, ' '.join(getattr(self, 'board')))
        gf.check_initialized()
        return gf

    @property
    def _isWon(self):
        """when the tic-tac-toe game comes to a winning connection"""
        return (self.board[0] == self.board[4] == self.board[8] != '' or
            self.board[2] == self.board[4] == self.board[6] != '' or
            self.board[0] == self.board[1] == self.board[2] != '' or
            self.board[3] == self.board[4] == self.board[5] != '' or
            self.board[6] == self.board[7] == self.board[8] != '' or
            self.board[0] == self.board[3] == self.board[6] != '' or
            self.board[1] == self.board[4] == self.board[7] != '' or
            self.board[2] == self.board[5] == self.board[8] != '')


class Move(ndb.Model):
    """A Kind to record each move of a Game, call with Game as parent"""
    moveNumber = ndb.IntegerProperty()
    playerName = ndb.StringProperty()
    positionTaken = ndb.IntegerProperty()

    @property
    def _copyMoveToForm(self):
        """Copy relevant fields from Move to MoveForm."""
        mf = MoveForm()
        # all_fields: Gets all field definition objects. Returns an iterator
        # over all values in arbitrary order.
        for field in mf.all_fields():
            if hasattr(self, field.name):
                setattr(mf, field.name, getattr(self, field.name))
        mf.check_initialized()
        return mf


class PlayerMiniForm(messages.Message):
    """ as inbound request message"""
    displayName = messages.StringField(1)


class PlayerForm(messages.Message):
    """as outbound response message"""
    userId = messages.StringField(1)
    displayName = messages.StringField(2)
    mainEmail = messages.StringField(3)
    gamesInProgress = messages.StringField(4, repeated=True)
    gamesCompleted = messages.StringField(5, repeated=True)
    # winsTotal = messages.IntegerField(6)
    # gamesTotal = messages.IntegerField(7)


class PlayerRankForm(messages.Message):
    """as outbound response message pertaining players' ranking"""
    displayName = messages.StringField(1)
    winsTotal = messages.IntegerField(2)
    mainEmail = messages.StringField(3)
    gamesTotal = messages.IntegerField(4)
    percentage = messages.FloatField(5)


class PlayersRankForm(messages.Message):
    """as outbound response message pertaining players' ranking"""
    items = messages.MessageField(PlayerRankForm, 1, repeated=True)


class GameForm(messages.Message):
    """outbound form message as response object"""
    websafeKey = messages.StringField(1)
    name = messages.StringField(2)
    seatsAvailable = messages.IntegerField(3)
    gameBoard = messages.StringField(4)
    playerOne = messages.StringField(5)
    playerTwo = messages.StringField(6)
    gameCurrentMove = messages.IntegerField(7)
    lastPlayer = messages.StringField(8)
    gameOver = messages.BooleanField(9)
    gameWinner = messages.StringField(10)


class GameMiniForm(messages.Message):
    """inbound form message for creating and participating game"""
    name = messages.StringField(1)


class GamesForm(messages.Message):
    """ multiple game outbound form message as response object"""
    items = messages.MessageField(GameForm, 1, repeated=True)


class MoveForm(messages.Message):
    """outbound form message as response object after making a move"""
    moveNumber = messages.IntegerField(1)
    playerName = messages.StringField(2)
    positionTaken = messages.IntegerField(3)


class MovesForm(messages.Message):
    """outbound message as response object of a game history query"""
    items = messages.MessageField(MoveForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    data = messages.StringField(1, required=True)


class BooleanMessage(messages.Message):
    """BooleanMessage-- outbound Boolean value message"""
    data = messages.BooleanField(1)

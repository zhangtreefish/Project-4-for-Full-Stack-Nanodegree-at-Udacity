import httplib
import endpoints
from protorpc import messages
from google.appengine.ext import ndb

class ConflictException(endpoints.ServiceException):
    """ConflictException -- exception mapped to HTTP 409 response"""
    http_status = httplib.CONFLICT

class PositionNumber(messages.Enum):
    """To denote the player and game piece during the moves"""
    NOT_SPECIFIED = 1
    position1A = 2
    position1B = 3
    position1C = 4
    position2A = 5
    position2B = 6
    position2C = 7
    position3A = 8
    position3B = 9
    position3C = 10

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
        gamesWon = set()
        for g in self.gamesCompleted:
            game = ndb.Key(urlsafe=g).get()
            if game and game.gameWinner==self.displayName:
                gamesWon.add(g)

        winsTotal = len(gamesWon)
        gamesTotal = len(self.gamesCompleted)
        percentage = 0.00
        # rounded_pct = 0
        if gamesTotal!=0:
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
    position1A = ndb.StringProperty()
    position1B = ndb.StringProperty()
    position1C = ndb.StringProperty()
    position2A = ndb.StringProperty()
    position2B = ndb.StringProperty()
    position2C = ndb.StringProperty()
    position3A = ndb.StringProperty()
    position3B = ndb.StringProperty()
    position3C = ndb.StringProperty()
    # moveLogs = ndb.StructuredProperty(Move, repeated=True)
    gameCurrentMove = ndb.IntegerProperty(default=0)
    lastPlayer = ndb.StringProperty()
    gameOver = ndb.BooleanProperty(default=False)
    gameWinner = ndb.StringProperty()
    # gameCancelled = ndb.BooleanProperty()

    @property
    def _copyGameToForm(self):
        """Copy relevant fields from Game to GameForm."""
        gf = GameForm()
        for field in gf.all_fields():
            if hasattr(self, field.name):
                setattr(gf, field.name, getattr(self, field.name))
            elif field.name == "websafeKey":
                setattr(gf, field.name, self.key.urlsafe())
        gf.check_initialized()
        return gf

    @property
    def _isWon(self):
        """when the tic-tac-toe game comes to a winning connection"""
        return (self.position1A==self.position2B==self.position3C!=None or
            self.position1A==self.position2B==self.position3C!=None or
            self.position1A==self.position1B==self.position1C!=None or
            self.position2A==self.position2B==self.position2C!=None or
            self.position3A==self.position3B==self.position3C!=None or
            self.position1A==self.position2A==self.position3A!=None or
            self.position1B==self.position2B==self.position3B!=None or
            self.position1C==self.position2C==self.position3C!=None)


class Move(ndb.Model):
    """A Kind to record each move of a Game, call with Game as parent"""
    moveNumber = ndb.IntegerProperty()
    playerName = ndb.StringProperty()
    positionTaken = ndb.StringProperty()

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
    gamesTotal = messages.IntegerField(3)
    percentage = messages.FloatField(4)


class PlayersRankForm(messages.Message):
    """as outbound response message pertaining players' ranking"""
    items = messages.MessageField(PlayerRankForm, 1, repeated=True)


class GameForm(messages.Message):
    """outbound form message as response object"""
    seatsAvailable = messages.IntegerField(1)
    playerOne = messages.StringField(2)
    playerTwo = messages.StringField(3)
    position1A = messages.StringField(4)
    position1B = messages.StringField(5)
    position1C = messages.StringField(6)
    position2A = messages.StringField(7)
    position2B = messages.StringField(8)
    position2C = messages.StringField(9)
    position3A = messages.StringField(10)
    position3B = messages.StringField(11)
    position3C = messages.StringField(12)
    gameOver = messages.BooleanField(13)
    gameCurrentMove = messages.IntegerField(14)
    websafeKey = messages.StringField(15)
    name = messages.StringField(16)
    lastPlayer = messages.StringField(17)


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
    positionTaken = messages.StringField(3)


class MovesForm(messages.Message):
    """outbound message as response object of a game history query"""
    items = messages.MessageField(MoveForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    data = messages.StringField(1, required=True)

#!/usr/bin/env python

import httplib
import endpoints
from protorpc import messages
from google.appengine.ext import ndb


class PlayerNumber(messages.Enum):
    """To denote the player and game piece during the moves"""
    NOT_SPECIFIED = 1
    One = 2
    Two = 3


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


class ConflictException(endpoints.ServiceException):
    """ConflictException -- exception mapped to HTTP 409 response"""
    http_status = httplib.CONFLICT


class Player(ndb.Model):
    """A Kind to represent player profile"""
    # Id = ndb.StringProperty()  # Should  Id be here or not?
    # use MD5 hash of the email to use as id
    displayName = ndb.StringProperty()
    mainEmail = ndb.StringProperty()
    gamesInProgress = ndb.StringProperty(repeated=True)  # games that she plays
    gamesCompleted = ndb.StringProperty(repeated=True)
    # winsTotal = ndb.IntegerProperty()
    # gamesTotal = ndb.IntegerProperty()


class Move(ndb.Model):
    """A Kind to record each move of a Game, call with Game as parent"""
    moveNumber = ndb.IntegerProperty()
    playerNumber = ndb.StringProperty()
    positionTaken = ndb.StringProperty()


class Game(ndb.Model):
    """A Kind for Game, instantiate with Player as parent"""
    seatsAvailable = ndb.IntegerProperty(default=2)
    playerOneId = ndb.StringProperty()
    playerTwoId = ndb.StringProperty()
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
    # TODO: winner here, or the player of the last move of completed games


class MoveForm(messages.Message):
    """outbound form message as response object after making a move"""
    moveNumber = messages.IntegerField(1)
    playerNumber = messages.EnumField(PlayerNumber, 2)
    positionTaken = messages.EnumField(PositionNumber, 3)


class MovesForm(messages.Message):
    """outbound message as response object of a game history query"""
    items = messages.MessageField(MoveForm, 1, repeated=True)

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


class GameForm(messages.Message):
    """outbound form message as response object"""
    seatsAvailable = messages.IntegerField(1)
    playerOneId = messages.StringField(2)
    playerTwoId = messages.StringField(3)
    # position1A = messages.EnumField(PlayerNumber, 4)
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
    # playerCurrentTurn = messages.EnumField(PlayerNumber, 16)
    # moveLogs = messages.MessageField(MoveForm, 16, repeated=True)


class GamesForm(messages.Message):
    """ multiple game outbound form message as response object"""
    items = messages.MessageField(GameForm, 1, repeated=True)


class GameQueryForm(messages.Message):
    """ as request object-- query inbound form message"""
    field = messages.StringField(1)
    operator = messages.StringField(2)
    value = messages.StringField(3)


class GameQueryForms(messages.Message):
    """ as request object-- multiple GameQueryForm inbound form message"""
    filters = messages.MessageField(GameQueryForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    data = messages.StringField(1, required=True)


# needed for conference registration
class BooleanMessage(messages.Message):
    """BooleanMessage-- outbound Boolean value message"""
    data = messages.BooleanField(1)

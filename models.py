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
    OneA = 2
    OneB = 3
    OneC = 4
    TwoA = 5
    TwoB = 6
    TwoC = 7
    ThreeA = 8
    ThreeB = 9
    ThreeC = 10


class ConflictException(endpoints.ServiceException):
    """ConflictException -- exception mapped to HTTP 409 response"""
    http_status = httplib.CONFLICT


class Player(ndb.Model):
    """A Kind to represent player profile"""
    # Id = ndb.StringProperty()  # Should  Id be here or not?
    # use MD5 hash of the email to use as id
    displayName = ndb.StringProperty()
    mainEmail = ndb.StringProperty()
    gamesInProgress = ndb.StringProperty(repeated=True)
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
    seatsAvailable = ndb.IntegerProperty()
    playerOneId = ndb.StringProperty()
    playerTwoId = ndb.StringProperty()
    positionOneA = ndb.StringProperty()
    positionOneB = ndb.StringProperty()
    positionOneC = ndb.StringProperty()
    positionTwoA = ndb.StringProperty()
    positionTwoB = ndb.StringProperty()
    positionTwoC = ndb.StringProperty()
    positionThreeA = ndb.StringProperty()
    positionThreeB = ndb.StringProperty()
    positionThreeC = ndb.StringProperty()
    moveLogs = ndb.StructuredProperty(Move, repeated=True)
    gameCurrentMove = ndb.IntegerProperty()
    playerCurrentTurn = ndb.StringProperty()
    gameOver = ndb.BooleanProperty()
    # gameCancelled = ndb.BooleanProperty()


class MoveForm(messages.Message):
    """outbound form message as response object after making a move"""
    moveNumber = messages.IntegerField(1)
    playerNumber = messages.EnumField(PlayerNumber, 2)
    positionTaken = messages.EnumField(PositionNumber, 3)


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
    position1A = messages.EnumField(PlayerNumber, 4)
    position1B = messages.EnumField(PlayerNumber, 5)
    position1C = messages.EnumField(PlayerNumber, 6)
    position2A = messages.EnumField(PlayerNumber, 7)
    position2B = messages.EnumField(PlayerNumber, 8)
    position2C = messages.EnumField(PlayerNumber, 9)
    position3A = messages.EnumField(PlayerNumber, 10)
    position3B = messages.EnumField(PlayerNumber, 11)
    position3C = messages.EnumField(PlayerNumber, 12)
    gameOver = messages.BooleanField(13)
    gameCurrentMove = messages.IntegerField(14)
    websafeKey = messages.StringField(15)
    playerCurrentTurn = messages.EnumField(PlayerNumber, 16)
    moveLogs = messages.MessageField(MoveForm, 17, repeated=True)


class GameForms(messages.Message):
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

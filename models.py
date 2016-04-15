#!/usr/bin/env python

import httplib
import endpoints
from protorpc import messages
from google.appengine.ext import ndb

class ConflictException(endpoints.ServiceException):
    """ConflictException -- exception mapped to HTTP 409 response"""
    http_status = httplib.CONFLICT

class Player(ndb.Model):
    """Player kind, to represent player profile"""
    # Id = ndb.StringProperty()  # Should  Id be here or not?
    # use MD5 hash of the email to use as id
    displayName = ndb.StringProperty()
    mainEmail = ndb.StringProperty()
    gamesInProgress = ndb.StringProperty(repeated=True)
    gamesCompleted = ndb.StringProperty(repeated=True)
    # winsTotal = ndb.IntegerProperty()
    # gamesTotal = ndb.IntegerProperty()

class Game(ndb.Model):
    """Game kind, to generate game entities with"""
    seatsAvailable = ndb.IntegerProperty()
    playerOneId = ndb.StringProperty()
    playerTwoId = ndb.StringProperty()
    gameCurrentMove = ndb.IntegerProperty()
    positionOneA = ndb.StringProperty()
    positionOneB = ndb.StringProperty()
    positionOneC = ndb.StringProperty()
    positionTwoA = ndb.StringProperty()
    positionTwoB = ndb.StringProperty()
    positionTwoC = ndb.StringProperty()
    positionThreeA = ndb.StringProperty()
    positionThreeB = ndb.StringProperty()
    positionThreeC = ndb.StringProperty()
    gameOver = ndb.BooleanProperty()
    # gameCancelled = ndb.BooleanProperty()

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
    playerOneId = messages.StringField(1)
    playerTwoId = messages.StringField(2)
    gameCurrentMove = messages.IntegerField(3)
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
    websafeKey = messages.StringField(14)
    seatsAvailable = messages.IntegerField(15)


class MoveForm(messages.Message):
    """inbound form message as request object for making a move"""
    playerId = messages.StringField(1)
    positionPlayed = messages.StringField(2)

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

class GamePiece(messages.Enum):
    """-- one of the two players enumeration value"""
    NOT_SPECIFIED = 1
    Red = 2
    Blue = 3

# needed for conference registration
class BooleanMessage(messages.Message):
    """BooleanMessage-- outbound Boolean value message"""
    data = messages.BooleanField(1)

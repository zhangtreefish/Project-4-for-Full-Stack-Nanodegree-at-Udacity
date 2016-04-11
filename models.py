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
    displayName = ndb.StringProperty()
    mainEmail = ndb.StringProperty()
    gamesInProgress = ndb.StringProperty(repeated=True)
    gamesCompleted = ndb.StringProperty(repeated=True)
    winTotal = ndb.IntegerProperty()
    gameTotal = ndb.IntegerProperty()

class Game(ndb.Model):
    """Game kind, to generate game entities with"""
    playerOneId = ndb.StringProperty()
    playerTwoId = ndb.StringProperty()
    gameTotalMoves = ndb.IntegerProperty()
    position1A = ndb.StringProperty()
    position1B = ndb.StringProperty()
    position1C = ndb.StringProperty()
    position2A = ndb.StringProperty()
    position2B = ndb.StringProperty()
    position2C = ndb.StringProperty()
    position3A = ndb.StringProperty()
    position3B = ndb.StringProperty()
    position3C = ndb.StringProperty()
    gameOver = ndb.BooleanProperty()

class PlayerMiniForm(messages.Message):
    """ as inbound request message"""
    displayName = messages.StringField(1)

class PlayerForm(messages.Message):
    """as outbound response message"""
    userId = messages.StringField(1)
    displayName = messages.StringField(2)
    mainEmail = messages.StringField(3)

class GameForm(messages.Message):
    """outbound form message as response object"""
    name            = messages.StringField(1)
    description     = messages.StringField(2)
    organizerUserId = messages.StringField(3)
    topics          = messages.StringField(4, repeated=True)
    city            = messages.StringField(5)
    startDate       = messages.StringField(6)
    month           = messages.IntegerField(7, variant=messages.Variant.INT32)
    maxAttendees    = messages.IntegerField(8, variant=messages.Variant.INT32)
    seatsAvailable  = messages.IntegerField(9, variant=messages.Variant.INT32)
    endDate         = messages.StringField(10)
    websafeKey      = messages.StringField(11)
    organizerDisplayName = messages.StringField(12)

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

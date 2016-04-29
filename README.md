
# How to Use this API
1. To test the API: visit https://tictactoe-2016.appspot.com/_ah/api/explorer
2. If choosing to download the code and test the API locally for yourself:
  -- Update the value of application in app.yaml to the app ID you have
   registered in the App Engine admin console if you would like to host your
   instance of this sample.
  -- Run the app with the devserver using 'dev_appserver.py DIR', and go to
   http://localhost:8080/_ah/api/explorer, and do the following:
   In Windows press the window button and 'r' at the same time, and enter in
    the resulting box:
     "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --incognito
     --user-data-dir=%TMP%
     --unsafely-treat-insecure-origin-as-secure=http://localhost:8080
     http://localhost:8080/_ah/api/explorer
  -- Optionally start the app with Google App Engine Launcher. See References/
   setup/7 for detailed steps.

# How to Play My Tic-tac-toe Game
1. User has to authenticate to play.
2. User creates player by 'create_player';
2. Player creates a game by 'create_game';
3. Sign up for a game by 'participate_game', need to enter the 'websafeGameKey'
   of the intended game;use 'all_games' to pick a game key, and get_game to get
   game information.
4. A game can be played when two players have signed up.
5. A player plays by 'make_move': again need to enter the 'websafeGameKey'.
   For positionTaken pick any number from 0-8, with 0-2, 3-5, and 6-8
   representing the 1st, 2nd, and 3rd row respectively, within each row with
   the number representing the grid from the left to right.
6. A player wins by connecting three grids in a straight line before the
   opponent.

## API endpoints and involved requests
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

    @endpoints.method(GAME_CREATE_REQUEST, GameForm,
                      path='create_game',
                      http_method='POST',
                      name='create_game')
    def createGame(self, request):
        """
        a player creates a game of a unique name
        """

    @endpoints.method(message_types.VoidMessage, GamesForm,
                      path='all_games', http_method='GET', name='all_games')
    def allGames(self, request):
        """
        This returns all games ever created by anyone on this app, sorted by
        seatsAvailable.
        """

    @endpoints.method(GAME_JOIN_REQUEST, GameForm,
                      path='participate_game/{websafeGameKey}',
                      http_method='POST',
                      name='participate_game')
    def participateGame(self, request):
        """
        Sign a player(identifiable by player_name) up for a game (identifiable
        by key); can not play against self
        """

    @endpoints.method(GAME_GET_REQUEST, GameForm,
                      path='game/{websafeGameKey}',
                      http_method='GET', name='get_game')
    def getGame(self, request):
        """Return requested game (by websafeGameKey)."""

    @endpoints.method(GAME_JOIN_REQUEST, GameForm,
                      path='cancel_game/{websafeGameKey}',
                      http_method='DELETE', name='cancel_game')
    def cancelGame(self, request):
        """
        Cancels a user from a game if the game is not complete AND no player
        has ever made a first move.
        """

    @endpoints.method(PLAYER_MINI_REQUEST, GamesForm,
                      path='games', http_method='GET', name='get_user_games')
    def getPlayerGames(self, request):
        """
        This returns all games a player has signed up for but has not
        completed, i.e., those in the gamesInProgress list.
        """

    @endpoints.method(GAME_MOVE_REQUEST, GameForm,
                      path='make_move/{websafeGameKey}/{positionTaken}',
                      http_method='POST',
                      name='make_move')
    def makeMove(self, request):
        """
        authenticated player makes a move, implemented by creating a move,
         updating Game and Player
        """

    @endpoints.method(message_types.VoidMessage, BooleanMessage,
                      path='delete_all_games', http_method='POST',
                      name='delete_all_games')
    def deleteAllGames(self, request):
        """
        deleting all Games created by current player, except those that are
        played.
        """

    @endpoints.method(message_types.VoidMessage, PlayersRankForm,
                      path='players_ranking', http_method='GET',
                      name='get_user_rankings')
    def getPlayerRankings(self, request):
        """
        a list consisting of each Player's name and the winning percentage
        """

    @endpoints.method(GAME_GET_REQUEST, MovesForm,
                      path='game_history/{websafeGameKey}',
                      http_method='GET', name='get_game_history')
    def getGameHistory(self, request):

    @staticmethod
    def _cacheAnnouncement():
        """Create Announcement & assign to memcache; used by
        memcache cron job & putAnnouncement().
        """

    @endpoints.method(message_types.VoidMessage, StringMessage,
                      path='tictactoe/announcement/get',
                      http_method='GET', name='getAnnouncement')
    def getAnnouncement(self, request):
        """Return Announcement from memcache."""

## Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Serves emails through taskqueue handlers.
 - models.py: Kind and Message definitions including helper methods.
 - gitignore
 - README.md
 - Design.md: Reflections on the design and development of the application.
 - setting.py

## Models Included:
 - **Player**
    - Requires unique user_name and email address.

 - **Game**
    - Stores game name and game states. Entities created with Player as parent.

 - **Move**
    - Records the number,player and played position of each move. Entities
      created with Game as parent

# References
## Products
- [App Engine][1]
## Language
- [Python][2]
## APIs
- [Google Cloud Endpoints][3]
## Setup
1. registered in the App Engine admin console, get application-id
2. Update the value of `application` in `app.yaml` to the application-id <like
   my 'tictactoe-2016'>
3. Go to Google [Developer Console][4], select the project<like my 'tictactoe'>
  -- select Enable and manage APIs
  -- select Credentials from the left-hand column
  -- Follow the instructions below for updating the user consent screen and
  creating the correct credentials [Creating an OAuth 2.0 web client ID][7]
    -- User Consent Screen
      -- Click the OAuth consent screen tab
      -- Select an Email address that you want associated with the app
    -- Include a Product name
    -- Click Save Credentials

  -- Click the Credentials tab
    -- Select Add credentials and choose OAuth 2.0 client ID
    -- Select Web application for the Application type
    -- In the Authorized JavaScript origins field include these two URLs:
    https://YOUR_PROJECT_ID.appspot.com/ and http://localhost:8080 (be sure to
     replace 8080 with the port for your application)
    -- In the Authorized redirect URIs field include these two URLs:
    https://YOUR_PROJECT_ID.appspot.com/oauth2callback and
    http://localhost:8080/oauth2callback (be sure to replace 8080 with the
    port for your application)
    -- Click Create, receiving client id and client secret.
4. Update the values at the top of `settings.py` to reflect the respective
client IDs.
      -- Copy the long client ID that ends with "googleusercontent.com""
      -- Go to your settings.py file, replace the string 'replace with Web
      client ID' with your client ID as a string; save settings.py
5. Update the value of CLIENT_ID in `static/js/app.js` to the Web client ID
6. (Optional) Mark the configuration files as unchanged as follows:
   $ git update-index --assume-unchanged app.yaml settings.py static/js/app.js
7. Run the app with the devserver using `dev_appserver.py DIR`, and ensure it's
  running by visiting your local server's address (by default [localhost:8080]
  [5].)
8. Generate your client library(ies) with [the endpoints tool][6].
9. Deploy your application.

10. How to Deploy the Application
1). Download and install Google App Engine SDK for Python from
   https://cloud.google.com/appengine/downloads#Google_App_Engine_SDK_for_
   Python.
2). In App Engine launcher, make sure there is no other application; click
  'File/Add Existing Application' tab, and 'browse' to the project folder
   (where the tictactoe project is), click "Add", "Run", "Browse",and if all
   is working, "Deploy".

[1]: https://developers.google.com/appengine
[2]: http://python.org
[3]: https://developers.google.com/appengine/docs/python/endpoints/
[4]: https://console.developers.google.com/
[5]: https://localhost:8080/
[6]: https://developers.google.com/appengine/docs/python/endpoints/endpoints_tool
[7]: https://cloud.google.com/appengine/docs/python/endpoints/auth
[8]: http://lifehacker.com/compare-the-contents-of-two-folders-with-the-diff-comma-598872057
[9]: http://pep8online.com/
[10]:http://stackoverflow.com/
[11]: http://stackoverflow.com/questions/5893163/what-is-the-purpose-of-the-single-underscore-variable-in-python
[12]: https://cloud.google.com/appengine/docs/python/taskqueue/push/creating-push-queues

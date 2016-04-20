# How to Use this API
1. To test the API: visit https://tictactoe-2016.appspot.com/_ah/api/explorer
2. If choosing to download the code and launch Chrome to test the API locally,
   go to http://localhost:8080/_ah/api/explorer, and do the following:
   In Windows press the window button and 'r' at the same time, and enter in
    the resulting box:
     "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --incognito
     --user-data-dir=%TMP%
     --unsafely-treat-insecure-origin-as-secure=http://localhost:8080
     http://localhost:8080/_ah/api/explorer

# How to Play My Tic-tac-toe Game
1. User has to authenticate to play by 'getPlayer';
2. Create a game by 'createGame'; or do 'getPlayer' to view game keys already
   created
3. Sign up for a game by 'participateGame', need to enter the 'websafeGameKey'
   of the intended game;
4. Play by 'MakeMove': need to enter the 'websafeGameKey';use 'getPlayerGames',
   'queryGames', or 'allGames' to find a game key

# Reference:
1. http://pep8online.com/
2. http://stackoverflow.com/
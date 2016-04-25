
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
1. User has to authenticate to play by 'getPlayer';
2. Create a game by 'createGame'; or do 'getPlayer' to view game keys already
   created
3. Sign up for a game by 'participateGame', need to enter the 'websafeGameKey'
   of the intended game;
4. Play by 'MakeMove': need to enter the 'websafeGameKey';use 'getPlayerGames',
   'queryGames', or 'allGames' to find a game key

## References

# Products
- [App Engine][1]

# Language
- [Python][2]

# APIs
- [Google Cloud Endpoints][3]

# Setup
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

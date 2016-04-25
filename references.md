App Engine application for the Udacity training course.

## Products
- [App Engine][1]

## Language
- [Python][2]

## APIs
- [Google Cloud Endpoints][3]

## Setup
1. registered in the App Engine admin console, get application-id
2. Update the value of `application` in `app.yaml` to the application-id 'tictactoe-2016'
3. Go to Google [Developer Console][4], select my project 'tictactoe'
  -- select Enable and manage APIs
  -- select Credentials from the left-hand column
  -- Follow the instructions below for updating the user consent screen and creating the correct
     credentials [Creating an OAuth 2.0 web client ID][7]
    -- User Consent Screen
      -- Click the OAuth consent screen tab
      -- Select an Email address that you want associated with the app
    -- Include a Product name
    -- Click Save Credentials

  -- Click the Credentials tab
    -- Select Add credentials and choose OAuth 2.0 client ID
    -- Select Web application for the Application type
    -- In the Authorized JavaScript origins field include these two URLs: https://YOUR_PROJECT_ID.appspot.com/ and http://localhost:8080 (be sure to replace 8080 with the port for your application)
    -- In the Authorized redirect URIs field include these two URLs: https://YOUR_PROJECT_ID.appspot.com/oauth2callback and http://localhost:8080/oauth2callback (be sure to replace 8080 with the port for your application)
    -- Click Create, receiving client id and client secret.
4. Update the values at the top of `settings.py` to reflect the respective client IDs.
      -- Copy the long client ID that ends with "googleusercontent.com""
      -- Go to your settings.py file, replace the string 'replace with Web client ID' with your
         client ID as a string; save settings.py
5. Update the value of CLIENT_ID in `static/js/app.js` to the Web client ID
6. (Optional) Mark the configuration files as unchanged as follows:
   `$ git update-index --assume-unchanged app.yaml settings.py static/js/app.js`
7. Run the app with the devserver using `dev_appserver.py DIR`, and ensure it's running by visiting
   your local server's address (by default [localhost:8080][5].)
8. Generate your client library(ies) with [the endpoints tool][6].
9. Deploy your application.

## How to Deploy the Application
1. Download and install Google App Engine SDK for Python from https://cloud.google.com/appengine/downloads#Google_App_Engine_SDK_for_Python.
2. In App Engine launcher, make sure there is no other application; click 'File/Add Existing Application' tab, and 'browse' to the project folder (where the tictactoe project is), click "Add'.

[1]: https://developers.google.com/appengine
[2]: http://python.org
[3]: https://developers.google.com/appengine/docs/python/endpoints/
[4]: https://console.developers.google.com/
[5]: https://localhost:8080/
[6]: https://developers.google.com/appengine/docs/python/endpoints/endpoints_tool
[7]: https://cloud.google.com/appengine/docs/python/endpoints/auth
[8]: http://lifehacker.com/compare-the-contents-of-two-folders-with-the-diff-comma-598872057
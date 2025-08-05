# Google Oauth Tutorial
In this tutorial, you'll figure out how to create your own Google OAUTH client.

## Step 1
* Go to the Google Cloud Console
    * You can just search up **Google Cloud Console** and click on the first link
    * If you haven't created an account, you'll have to create one here
* Click on the three horizontal lines on the top left corner of the page
* Click on the tab labeled **APIs & Services**

## Step 2
* On the lefthand side, you will see a dropdown menu that has the following tabs:
    * Enabled APIs & services
    * Library
    * Credentials
    * OAuth consent screen
    * Page usage agreements
* Select the one titled **OAuth consent screen**

## Step 3
* On the sidebar, click the tab labeled **Clients**
* If you have never created a client before, your page will say "Google Auth Platform not configured yet"
    * Click on the blue button that says **Get Started**
* If you have created a client, you will see a table of the clients you have created
    * Above this table will be a button saying **+ Create Client**
    * Click on that

## Step 4
The following information is for people who have never created a client before. If you have created a client, please refer to step 5. 
* After clicking **Get Started**, you'll have to fill out 4 fields, which are:
    * App information
    * Audience
    * Contact Information
    * Finish
* App information: name you app, maybe ucr-chatbot-proto, and put in a good email for you
* Audience: click external
* Contact information: put a good email for you, again
* Finish: agree to the statement
* Click create
* You will then be directed to a page with **Metrics** and "Project Checkup"
* Click "Create OAuth client" under **Metrics**

## Step 5
The people who have never created a client and the people who have should be in synch in this step.
* You will see a page that is titled **Create OAuth client ID**
* Click on the **Application type** dropdown and select **Web application**
* Then, when the **Name** field opens, you can name your client whatever you want
* Scroll down to where it says "Authorized redirect URIs"
* Put in: http://127.0.0.1:5000/authorize/google
* Hit save

## Step 6
* On the side of the page, click on the tab that says **Audience**
* Scroll down to where it says **Test users**
* Click on the button that says **Add users**
    * Here, you can any email
    * Add one that you want to test with the database
* Hit save

## Step 7
* Go back to the tab on the sidebar called **Clients**
* Now, you should see a table with your client on it
* Click on your client
* On the right side, you will see a section called **Additional Information**
* Copy your client ID and client secret and put them in your .env folder
    * In your folder, it should look like this:
        * export GOOGLE_CLIENT_ID="your google client id"
        * export GOOGLE_SECRET="your client secret"

## Congrats!
You have just created your Google OAuth client! Hopefully this tutorial was helpful!
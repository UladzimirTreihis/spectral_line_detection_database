# CO_database_project
available at https://linedb.nfshost.com/

### User / Admin Manual.

I. Getting started.
    1. Creating an account.
In order to use most of the functionalities provided by this web app, you should create an account by clicking register. Please enter your real email address as the confirmation instructions will be automatically sent out by the app. Please check your email to click the confirmation link. 
    2. Logging in.
Once you have confirmed your email you will be automatically redirected to the web app. You will be using your email address and the password to log-in from any device. We only store the essential data such as your credentials in encrypted format in order to keep track of submissions that belong to you, and thus, identify submissions. By clicking my profile you can see the data associated with you. If you wish, you could add more info about you such as your institution.
    3. If you have any questions throughout the process, contact us using the info in the Contact Us section. 
II. Browsing and accessing data.
    1. You can access the list of all galaxies and their corresponding detection by navigating to View Database. Each galaxy name is a clickable link that will lead you to the corresponding page of this galaxy. 
    2. You can search for specific detections using our Advanced Search feature. Enter only those parameters that you are interested in specifying. 
    3. You can download a csv file with all our database or some specific galaxies and their detections.
III. Submitting data.
    1. The submission instructions are under the Contribute Data page.  
IV. Approving data (for Admins). 
    1. If your account has admin privileges (contact us to request for the admin account), you will see a button called “Go to Admin”. 
    2. Clicking on “Submissions”, you can select and either approve or delete submissions. 




### Developer Manual.

The app is based on the FLASK framework using SQLAlchemy for managing database commands and SQLite3 database. The app is employing several Blueprints, which is a good practice for such a project. All functions and routes are explained using Docstrings. Contact us if you want to discuss the deployment.

FAQ:

1. What do I do if I want to continue developing the project?
	Fork the repo and push your features for review. Contacting the administrator could be useful to discuss the development beforehand. 
2. What are these folders in the project? 
	The folders follow the naming conventions of the hosting service. 
    	a) protected: all your flask code, routes and development will almost certainly happen here.
    	b) public: here you will find the html templates. If you just need to make a minor edit to the text / style, please refer here.
    	c) conf: here you will find a configuration file. It contains sensitive data, and thus, in the production will only be accessible to those, who have requested the access. In the development stage you may use the file committed to GitHub. Note that the email connection will not work unless you enter the proper configuration in config.json. 
    	d) temp: here is the app.db file, containing our data. For obvious reasons, please do not delete it from the server unless you have backed it up. 
	All these folders obviously have different access permissions.
3. Why are there two config files?
	One is where sensitive data is stored to set up database and flask instance, and one contain other less sensitive configuration for flask instance or constants that are easy to later import from the file. 
4. I made a change. How do I push it to the server? 
	First, we use nearlyfreespeech.net for hosting purposes. If you have been added to the users with access to the server, please do the following:
    	a) Make sure your change works for localhost. Test it manually under different conditions. 
    	b) If your change is a one liner, you can edit the code on the server with the nano text editor. If it is 1-5 files, you may delete the old copies from the server and upload your files from your local machine. We do not have anything like GitHub auto-updating service. Finally, if it is a big update over many files, just reupload the necessary folder(s). 
5. Have more questions? Contact me here: u.treihis@u.yale-nus.edu.sg



### Areas to consider for further development and bug fixing:

1. Advanced search
    a) The download results option.
2. Classification. 
    a) Currently classification is stored as a string and managed as a list of options throughout the application. A better (and easier for maintenance) practice would be creating a many to many relationship with a separate prefilled on startup table of classifications. 
    b) All routes that engage with classification will, therefore, have to be updated in the way they handle classification. 
3. Submissions
    a) Currently the submissions tab of the Admin side introduces only 3 pieces of information about each submission. Consider whether this is enough to make a decision (approve vs delete). The submission is not clickable and it is impossible to see all data in the submission. Thus, making them clickable or creating a button that retrieves more info on request might be preferred. 
    b) The submission page loads all submissions at once. For thousands of submissions this could significantly slow down the process of loading. Making the page load first N submissions and more on request could be preferred. 
    c) Submissions are automatically sorted by date. Alternatively, they should be sortable by user and type of submission (line / galaxy / edit). 
4. Main 
    a) The main page loads all galaxies at once. For thousands of galaxies this could significantly slow down the process of loading. Making the page load first N galaxies and more on request could be preferred. Moreover, the lines per species information is calculated each times on request.
5. Submit technical issue functionality.
    a) Currently all technical errors are automatically stored in the logs. However, checking them manually is not efficient. If one has encountered an error, being able to send a note to the admin would be helpful to direct for the solution and date + time in the logs. 
6. Coordinates.
    a) In fact, it does not yet support the 00d00’00’’ format, only 00d00m00s.
7. Reverse decision. 
    a) Currently there is no ability to reverse the commit on the database. And / or the ability to revert to the previous database version could be a plus.
8. Testing.
    a) Testing is in the development stage and has not been properly implemented. 

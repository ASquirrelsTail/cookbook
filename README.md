# Cookbook
 
## UX

A breakdown of the UX process can be found [here](https://github.com/ASquirrelsTail/cookbook/blob/master/preprod/ux.md).

## Features

### Existing Features

#### General Features

- The site features a responsive layout for use on a variety of devices.
- The site has a homepage with featured recipes and a selection of recent and popular recipes.
- Visitors can browse, filter and search recipes.
- Registered users can add recipes amongst other activites listed bellow.
- Users can crop and upload images to display with their recipes, with the option to use Amazon AWS S3 for data storage and retrieval. The crop and resize feature works on desktop and touch screen devices.
- An admin login allows a user to manage the site.
- The site has custom error pages to direct users to log in, or help them find the page they're looking for.

#### All Users

- Anybody can browse a list of all recipes on the site.
	- Recipes can be filtered based on a number of option such as tags and meals as well as ingredient text search.
	- Results can be ordered based on popularity, date or prep time.
- Anybody can register as a user on the site.

#### Registered Users

- Users can post and edit their own recipes, as well as delete them.
- They can "fork" or clone recipes created by others to put their own spin on them.
- Users can comment on the recipes of others and delete their own comments.
- They can favourite recipes, and filter and search their collection of favourited recipes.
- They can follow other users to have a feed of recipes from those they follow.
- They can set preferences to only see recipes that fit their filters on the main pages of the site, for example not showing recipes that contain nuts.

#### Admin Users

- Admins can select recipes to be featured on the front page.
- Admins can edit and delete anybody's recipes.
- They can delete anybody's comments.
- Admin users can add and remove tags and meals for filtering recipes.

### Features Left to Implement

- Passwords and password resets. These features fall outside the scope of the project, but can be implemented later.

## Technologies Used

- HTML5
- CSS3
- JavaScript
- Python3
- [Materialize 1.0.0](https://materializecss.com/)
	- The Materialize framework was used to establish the look and feel of the site. It provided a repsonsive layout, as well as various components and UI elements for the site. Additional styles were added through the use of SCSS, both to expand upon, and reduce the size of the css for the site.
- [Cash](https://kenwheeler.github.io/cash/)
	- Cash is used as an alternative to JQuery for DOM manipulation. It comes bundled with the latest version of Materialize, and has a much smaller footprint than JQuery.
- [Sass](https://sass-lang.com/)
	- Sass was used to preprocess and compile stylesheets for the site.
- [Flask 1.0.2](http://flask.pocoo.org/)
	- The Flask micro-framework serves the site over HTTP.
- [Jinja 2.10](http://jinja.pocoo.org/docs/2.10/)
	- The Jinja 2 templating language is used to create html templates and add content to the site.
- [MongoDB](https://www.mongodb.com/)
	- MongoDB handles the document based database for storing recipes and user information. The database for the main deployment is provided by the [MongoDB Atlas Cloud](https://www.mongodb.com/cloud) service.
- [AWS S3](https://aws.amazon.com/s3/)
	- Amazon AWS S3 storage was used to provide persistent storage for user images. The [Boto3 python API](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) was used to interface with the S3 service.
- [Pillow](https://pillow.readthedocs.io/en/stable/)
	- The updated version of the Python Imaging Library is used to validate images uploaded by users for size and type.
- [Unittest](https://docs.python.org/3/library/unittest.html)
	- Unittest is a testing framework which was used with Flask's test client to run automated tests on the application.

### Tools

- [Sublime Text 3.2.1](https://www.sublimetext.com/)
	- Sublime text was used to write the code for the site.
	- [Emmet](https://emmet.io/) package was used to speed up davelopment.
	- [HTML-CSS-JS Prettify](https://packagecontrol.io/packages/HTML-CSS-JS%20Prettify) package was used to prettify code layout.
	- [Anaconda](http://damnwidget.github.io/anaconda/) package was used as a PEP8 linter to write neater error free code.
- [GitHub](https://github.com/)
	- Git was used for version control, and GitHub was used for remote storage of repositories.
- [GIMP 2.10.8](https://www.gimp.org/)
	- GIMP 2 was used for image editing.
- [Inkscape](https://inkscape.org/)
	- Inkscape was used to create the logo and additional icons for the site.

## Testing

The site has been tested on a variety of devices, using different browsers and resolutions to ensure compatability and responsiveness.

HTML code was validated by the [WC3 Markup Validator](https://validator.w3.org/), as Jinja templates tend to cause confusion, the rendered templates of a selection of pages were fed into the validator instead.

CSS code was validated using the [WC3 CSS Validator](http://jigsaw.w3.org/css-validator/), and unsuprisingly passed, as it was generated by Sass.

Javascript was checked using [JSLint](https://www.jslint.com/), ignoring warnings about quote marks and line length no issues were raised.

Manual testing was used to test the front-end of the site, such as form validation and general functionality.

A test driven development process was followed for the backend, adding a test for each new feature and checking that test failed before doing what was necessary to ensure the test passed before repeating the process for the next feature. Once the test spec was developed and features implemented the code could be refactored and retested to ensure nothing broke. The whole test suite could be rerun after other features were added to ensure they didn't impact earlier features.

Example users were created to walk through the user stories established [here](https://github.com/ASquirrelsTail/cookbook/blob/master/preprod/ux.md).

User testing was employed once the site was feature complete to make sure it was easy to understand and use.

An in depth breakdown and examples of the testing approach can be found [here](https://github.com/ASquirrelsTail/cookbook/blob/master/tests/testing.md).

## Deployment

Code snippets that accompany the following instructions are for Linux systems, but commands are similar on other operating systems.

Before deploying the project the MongoDB database needs setting up, and, optionally, Amazon AWS S3.

### Database Setup

To store user data and recipes the project uses MongoDB, in order to run it you will need to set up a database. To do this you require the [Mongo Shell](https://www.mongodb.com/download-center/community?jmp=docs) installed, and either an installed version of MongoDB, or access to a cloud service such as MongoDB [Atlas](https://cloud.mongodb.com/).

First create a new database, and generate a [connection string](https://docs.mongodb.com/manual/reference/connection-string/) or URI for that database.

Next download the (init-mongo.js)[https://github.com/ASquirrelsTail/cookbook/blob/master/init-mongo.js] script, navigate to the directory containing it and run it using the Mongo Shell and your URI. Alternatively you can open the shell, connect to the database and run the script with the load() command.
```
$ mongo <MongoDB URI with your password and DB name> init-mongo.js
```

The script will create the required collections for the app to work, and add entries for an Admin user, and a selection of meal types and tags. The script also initialises a text index of the recipe title and ingredient fields to allow for text searches.

With the database set up its URI can now be passed as an environment variable for the app to use.

For larger databases it would also make sense to also add further indexes for various other fields, such as 'urn', 'username' and other commonly queried fields.

### AWS S3 Setup

To safely store user uploads the project utilises the Amazon AWS S3 cloud storage service. The project will run without it, and simply not declaring the AWS_BUCKET environment variable means that uploads will be stored locally in the static directory. However, this is an additional load on the Flask server to serve numerous large images, and where the project is deployed to a service like Heroku uploaded files will be lost when the file systems are replaced due to its [ephemeral file system](https://devcenter.heroku.com/articles/dynos#ephemeral-filesystem).

If you don't already have one, you can create a [free account on Amazon AWS](https://aws.amazon.com/). Log in to your AWS account, and select S3 from the list of services. If you don't already have S3 set up follow the instructions, you will be informed by email when the service is ready to go.

Create a new bucket, give it a unique name, and select a region. Using the same region your server will speed things up slightly. The name of this bucket will be used later as an environment variable.

You'll need to set permissions so anonymous users can have read access to your newly created bucket. Select your new bucket, click the permissions tab and select bucket policy. Set the following policy as per [Amazon's example](https://docs.aws.amazon.com/AmazonS3/latest/dev/example-bucket-policies.html#example-bucket-policies-use-case-2). Granting public access will come with a warning, but as it's only read access and these are only pictures of recipes you don't need to worry.
```
{
  "Version":"2019-06-16",
  "Statement":[
    {
      "Sid":"AddPerm",
      "Effect":"Allow",
      "Principal": "*",
      "Action":["s3:GetObject"],
      "Resource":["arn:aws:s3:::examplebucket/*"]
    }
  ]
}
```

You can test this by returning to the bucket's overview tab, uploading a file and selecting the file and following its Object URL. If everything has worked it should take you to the uploaded file. If not you will get permission denied notice.

With the bucket set up all that is left is to set up a user for the app to access S3. Select IAM from the list of services in AWS and navigate to the users section and select + New User.

Give the user a name, and select Programatic Access. On the next screen select create group, give the group a name, search the policy list for S3 and select AmazonS3FullAccess and click create group. Follow the remaining steps until the process is complete and you will be given an Access ID Key and a Secret Access Key, make a note of these as you will need them later to use as environment variables for setting up the app. If you lose your secret key you can create a new one at a later time by selecting the user in the IAM Service and clicking the Security Credentials tab.

With all this set up you should be able to fill in the S£ environment variables and use S3 for image storage within the app.

### Local Deployment

For local deplyoment you'll need [python3](https://www.python.org/downloads/), pip3 and the [Mongo Shell](https://www.mongodb.com/download-center/community) installed. You'll also need a MongoDB database, hosted either locally or on a cloud service such as [Atlas](https://cloud.mongodb.com/), follow the instructions in the Database Setup section to prepare this. Optionally you can use Amazon AWS S3 to host user images, follow the instructions in the AWS S3 Setup section to do so.

First create a directory and download or clone the project's GitHub Repository.
```
$ git clone https://github.com/ASquirrelsTail/cookbook.git
```

Next install the required python modules from the requirements.txt file using pip3.
```
$ sudo pip3 install -r requirements.txt
```

Follow the instructions for setting up your MongoDB database, in the Database Setup section.

Next set up environment variables, these can be saved to your .bashrc file, or simply input for the current session as follows.
```
$ export MONGO_URI="<MongoDB URI with your password and DB name>"
$ export SECRET_KEY="<Random string to use as Flasks Secret Key>"
```

Optionally if you are using AWS S3 to host user images follow the instructions in the AWS S3 Setup section. You'll also need to set the following environment variables. Leaving these unset means the app will save user images to the static folder instead.
```
$ export AWS_ACCESS_KEY_ID="<AWS access key ID for the user with AmazonS3FullAccess permissions>"
$ export AWS_SECRET_ACCESS_KEY="<AWS secret access key for the user with AmazonS3FullAccess permissions>"
$ export AWS_BUCKET="<Name of the S3 bucket you will be using>"
```

Finally running the app.py file from python will launch the flask server, and the site will be accessible at http://localhost:5000.
```
$ python3 app.py
```

### Remote Deployment

The site is deployed remotely on Heroku via GitHub. The repository already contains the necessary requirement.txt and Procfile files for Heroku deployment, the following steps were required to complete the process.

The project was pushed to GitHub, you can fork this repository to connect your own copy to Heroku.

Create a new app on Heroku, and connect it to the GitHub repo. Next go to settings and add the Python buildpack under the buildpacks options.

Follow the instructions to set up the MongoDB database in the Database Setup section and optionally set up Amazon AWS S3 for storing user images by following the instructions in the AWS S3 Setup section. If you don't set up AWS S3 for your Heroku deployment then user uploads will not persist when the dyno is restarted (which happens approximately once a day), which will lead to missing image files on recipe pages.

You will need to set the following config vars in the Heroku settings.
-MONGO_URI: <MongoDB URI with your password and DB name>
-SECRET_KEY: <Random string to use as Flasks Secret Key>
-AWS_ACCESS_KEY_ID: <AWS access key ID for the user with AmazonS3FullAccess permissions>
-AWS_SECRET_ACCESS_KEY: <AWS secret access key for the user with AmazonS3FullAccess permissions>
-AWS_BUCKET: <Name of the S3 bucket you will be using>
-IP: 0.0.0.0
-PORT: 8080

Finally on Heroku under the deploy tab either enable automatic deploys from the master branch, or select the master branch and deploy it manually. If all goes to plan you should be able to select Open App and launch the site.

## Known Issues

Text searches with multiple words ceases to utilise MongoDBs stemming and language features, as they must be wrapped in double quotes to ensure they are all included in the search to return relevant results. For instance the search string "apples" will return recipes containing the word apples, or apple, but the search "apples bannanas" will return only exact matches for "apples" and "bannanas", and will exclude recipes containing the words "apple" and "bannana".

Replacing the image for a parent recipe will also replace that of its children.

Cash and Materialize only supports IE11 and later, but this shouldn't affect too many users.

## Credits

### Code

The snippet to create an unsigned url for an S3 resource was from the solution on [this thread](https://github.com/boto/boto3/issues/110).

[This breakdown](https://css-tricks.com/custom-list-number-styling/) of adding custom numbers to lists was very helpful for the methods on recipe pages.

Patrick Kennedy's [blog post](https://www.patricksoftwareblog.com/unit-testing-a-flask-application/) on using unittest with python was a great help for setting up my tests.

### Content

Cookie policy wording and information used was from the [ICC Cookie Guide](https://www.cookielaw.org/media/1096/icc_uk_cookiesguide_revnov.pdf)

### Media

### Acknowledgements

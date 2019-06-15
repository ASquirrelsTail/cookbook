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
- Users can crop and upload images to display with their recipes, with the option to use Amazon AWS S3 for data storage and retrieval.
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

- Image crop that works with touch screens

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

A full breakdown and examples of the testing approach can be found [here](https://github.com/ASquirrelsTail/cookbook/blob/master/tests/testing.md).

The site has been tested on a variety of devices, using different browsers and resolutions to ensure compatability and responsiveness.

HTML code was validated by the [WC3 Markup Validator](https://validator.w3.org/), as Jinja templates tend to cause confusion, the rendered templates of a selection of pages were fed into the validator instead.

CSS code was validated using the [WC3 CSS Validator](http://jigsaw.w3.org/css-validator/), and unsuprisingly passed, as it was generated by Sass.

Javascript was checked using [JSLint](https://www.jslint.com/), ignoring warnings about quote marks and line length no issues were raised.

Manual testing was used to test the front-end of the site, such as form validation and general functionality.

A test driven development process was followed for the backend, adding a test for each new feature and checking that test failed before doing what was necessary to ensure the test passed before repeating the process for the next feature. Once the test spec was developed and features implemented the code could be refactored and retested to ensure nothing broke. The whole test suite could be rerun after other features were added to ensure they didn't impact earlier features.

Example users were created to walk through the user stories established [here](https://github.com/ASquirrelsTail/cookbook/blob/master/preprod/ux.md).

## Deployment


## Known Issues

Deleting a recipe means any parent or child recipes that referenced it will now link to a page that doen't exist.

Deleting a comment when another user has deleted a comment after you have loaded the page will result in the wrong comment being deleted due to the way comments are referenced by index.

Due to the use of ES6 let keyword, and object function declarations the site only supports IE11 and later. This could be ammended, however Cash and Materialize also only supports IE10 and later anyway. 

## Credits

### Snippets

The snippet to create an unsigned url for an S3 resource was from the solution on [this thread](https://github.com/boto/boto3/issues/110).

### Content

Cookie policy wording and information used was from the [ICC Cookie Guide](https://www.cookielaw.org/media/1096/icc_uk_cookiesguide_revnov.pdf)

### Media

### Acknowledgements

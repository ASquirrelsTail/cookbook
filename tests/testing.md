# Testing

## Automated Testing

The project employs automated testing for the python back end using the unittest framework and Flask's test client. The python back end was developed using a test driven development process, with an evolving test spec informing the development of new features. As more features are added or code is refactored the tests can be rerun to check all features still work.

The test script runs tests on routes in the application to ensure they respond as expected. It uses a live MongoDB database to make sure the correct changes are made to the database, and runs tests on rendered templates to check they contain information they are meant to. Testing the output of the app has the advantage that even if the underlying logic changes drastically, the site should still respond in the correct way.

### Testing Locally

To run the automated tests locally follow the instructions for [local deployment](https://github.com/ASquirrelsTail/cookbook/blob/master/README.md). For testing you can ommit the S3 environment variables, but including them will also work. In addition to that you will need a seperate MongoDB database, the URI for which should be in an environment variable called MONGO_TEST_URI. Don't use the same database as for a regular deployment, as the tests will delete all records in the test database. 
```
$ export MONGO_TEST_URI="<MongoDB URI with your password and test DB name>"
```

You will also require the unittest module.
```
$ sudo pip3 install unittest
```

Run the test_app.py file to run the tests, groups of tests for individual pages can be run by adding the test class as a command line argument.
```
$ python3 test_app.py TestAddRecipe
```

### Test Driven Development Example - The Recipe List Page

To begin I built a subclass of the TestClient class called TestRecipesList. This inherited the Flask test client and MongoDB setup from TestClient, as well as a series of helper functions for creating users, logging in and out, and submitting recipes. During the class set up stage the class empties then populates the MongoDB with recipes to use during testing.

```
$ python3 test_app.py TestRecipesList
.F
======================================================================
FAIL: test_page (__main__.TestRecipesList)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test_app.py", line 658, in test_page
    self.assertEqual(response.status_code, 200)
AssertionError: 404 != 200

----------------------------------------------------------------------
Ran 2 tests in 9.024s
```

The first test is to check the page exists and returns a status code of '200' when accessed. After checking this test fails I created the route in app.py, and ran the test again, and as expected it passed.

```
$ python3 test_app.py TestRecipesList
..
----------------------------------------------------------------------
Ran 2 tests in 4.703s

OK
```

The next series of tests check the page shows the number of recipes it has found. At first the page could simply be populated with the correct number to pass. As more tests were added to make them all pass required querying the database, so this was added to app.py.

When the test for multiple tags was added, it failed. Once I implemented the solution to query the MongoDB for multiple tags it passed, however the solution broke previous tests, as Mongo returns an error if you query using an array, but only give it a single value. This had to be fixed before all tests would pass again.
```
$ python3 test_app.py TestRecipesList
.E.E.
======================================================================
ERROR: test_number_of_multiple_tags (__main__.TestRecipesList)
----------------------------------------------------------------------
...
    return render_template('recipes.html', no_recipes=no_recipes)
UnboundLocalError: local variable 'no_recipes' referenced before assignment

======================================================================
ERROR: test_number_of_tagged_recipes (__main__.TestRecipesList)
----------------------------------------------------------------------
...
UnboundLocalError: local variable 'no_recipes' referenced before assignment

----------------------------------------------------------------------
Ran 5 tests in 4.781s

FAILED (errors=2)
```

The process continued as the recipes list route was expanded, with new tests being added, followed by code to make them pass. The tests and adjustments for the recipes list are documented in the git commits between commits 9bac94a and 93cf4b3 [here](https://github.com/ASquirrelsTail/cookbook/commits/master?before=26e619cee08b762460e46f66b2cd076fe79c8311+141). As development continued and other parts of the project were added and changed the entire test suite was rerun to make sure all functionality continued to work.

## Manual Testing

In addition to automated testing of the back end, manual testing was employed to find out if the front end was behaving as expected. At times manual testing also revealed issues missed by the test suite, so targeted tests could be added and fixes implemented.

Using the site in similar manner to the automated tests checked that the front end was passing the expected variables to the back end. For instance selected tags on the add-recipe page need to be converted to a string to be submitted and saved to the database, to check this I input the selected tags and submitted the recipe. Then I checked the recipe's page, and its entry in the database to make sure the result was as expected.

Tests of pages with validation were tested systematically by attempting to submit forms with misissng or malformed data, and making sure the page didn't submit the form, and gave an indication of the problem.

The image upload and edit functionality on the add-recipe page was tested manually with various sized and proportioned images to make sure it crops and resizes images appropriately.

## User Testing

As well as testing the usability of the site myself, I also had friends and family test the site once it was feature complete to make sure it was easy to understand and use.

Feedback was positive, and nothing broke. Interestingly the vast majority of users browed the site on their mobile phones.

A few minor UI changes were made to better accomodate mobile users based on their feedback, in particular adding words to buttons on the recipe pages which previously only featured icons, as these were not obvious to most users, and didn't convey a clear enough meaning to others.

Users often failed to find more advanced features, such as user pages and preferences, and didn't immediately understand the meaning of "forking" a recipe. However making these features more obvious would often detract from more important core features of the site.

## Testing Against User Stories

To ensure the site met requirements set out in the [user experience process](https://github.com/ASquirrelsTail/cookbook/blob/master/preprod/ux.md) the stories were acted out as follows:

- Sarah is searching for a quick meal to make for dinner.
  - On the recipes list page Sarah can sort recipes by "Quickest" to find herself a quick recipe.
- Ashley has a load of sweet potatoes and wants an interesting recipe to make the most of them.
  - Ashley can simply enter "sweet potatoes" into the seach box, and will be shown a variety of recipes containing sweet potato.
- Jessica is lactose intolerant, and doesn't want to be shown delicious looking recipes she can't have.
  - On the recipes page, Jessica can filter recipes by "Dairy Free", if she signs up and sets her preferences to include "Dairy Free" she will only see dairy free recipes when browsing the site (except where she's viewing a particular user's recipes, or has deselected "Dairy Free" in search results).
  - You can log in as Jessica to see this feature in action.
- Jeremy comes up with his own recipes, and wants feedback from other cooks.
  - Once he's signed up Jeremy is able to post recipes, and other users are able to favourite and comment to leave him feedback.
- Theresa wants to share some of her traditional recipes with the world.
  - After signing up Theresa is able to post her own recipes for people to enjoy.
- Ryan wants to keep up to date with recipes from cooks whos food he enjoys.
  - Ryan can sign up for an account and when he finds a cook he likes can select the follow button on their user page. Then his feed on the home page would be populated by recipes from these cooks.
  - You can log in as Ryan to see this feature in action.
- Mark likes to put his own spin on recipes, and once he's found something that works likes to come back and make it again.
  - After creating an account Mark can "fork" recipes from other users and put his unique spin on them.
  - He can favourite recipes he wants to come back to, and then filter by his favourites.
- Lauren enjoys veganising traditional recipes to share with her vegan friends.
  - Like Mark, Lauren can create an account and "fork" recipes, veganise them and add the "Vegan" tag to help others find them.


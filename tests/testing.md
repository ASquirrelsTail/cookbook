# Testing

## Automated Testing

The project employs automated testing for the python back end using the unittest framework and Flask's test client. The python back end was developed using a test driven development process, with an evolving test spec informing the development of new features. As more features are added or code is refactored the tests can be rerun to check all features still work.

The test script runs tests on routes in the application to ensure they respond as expected. It uses a live MongoDB database to make sure the correct changes are made to the database, and runs tests on rendered templates to check they contain information they are meant to. Testing the entire site and its output as opposed to specific functions has the advantage that even if the underlying logic changes drastically, the site should still respond in the correct way.

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

The process continued as the recipes list route was expanded, with new tests being added, followed by code to make them pass. The tests and adjustments for the recipes list are documented in the git commits between commits 9bac94a and 93cf4b3 [here](https://github.com/ASquirrelsTail/cookbook/commits/master?before=26e619cee08b762460e46f66b2cd076fe79c8311+141). As development continued and other parts of the project were added and changed the entire test suite was rerun to make sure all functionality still works.

## Manual Testing

In addition to automated testing of the back end, manual testing was employed to find out if the front end was behaving as expected. At times manual testing also revealed issues missed by the test suite, so targeted tests could be added and fixes implemented.

Using the site in similar manner to the automated tests checked that the front end was passing the expected variables to the back end. For instance selected tags on the add-recipe page need to be converted to a string to be submitted and saved to the database, to check this I input the selected tags and submitted the recipe. Then I checked the recipe's page, and its entry in the database to make sure the result was as expected.

Tests of pages with validation were tested systematically by attempting to submit forms with misissng or malformed data, and making sure the page didn't submit the form, and gave an indication of the problem.

The image upload and edit functionality on the add-recipe page was tested manually with various sized and proportioned images to make sure it crops and resizes images appropriately.

## User Testing

As well as testing the usability of the site myself, I also had friends and family test the site once it was feature complete to make sure it was easy to understand and use.
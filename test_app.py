import os
import unittest
import app

class TestApp(unittest.TestCase):
    def setUp(self):
        app.app.config['TESTING'] = True
        app.app.config['DEBUG'] = False
        # Use the test database URI instead of the default
        app.mongo = app.PyMongo(app.app, uri=os.getenv('MONGO_TEST_URI'))
        self.client = app.app.test_client()

        # Empty the "logins" collection
        app.mongo.db.logins.delete_many({})


    def test_home(self):
        response = self.client.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()

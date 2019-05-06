import os
import unittest
import app


def flask_test_client():
    '''
    Sets up flask testing client, changes MongoDB database to test database
    '''
    app.app.config['TESTING'] = True
    app.app.config['DEBUG'] = False
    # Use the test database URI instead of the default
    app.mongo = app.PyMongo(app.app, uri=os.getenv('MONGO_TEST_URI'))
    client = app.app.test_client()
    mongo = app.mongo

    return client, mongo


class TestApp(unittest.TestCase):
    def setUp(self):
        self.client, self.mongo = flask_test_client()
        self.mongo.db.logins.delete_many({})

    def create_user(self, username):
        '''
        Helper function to create a new user by sending a POST request to /new-user
        '''
        return self.client.post('/new-user', follow_redirects=True,
                                data={'username': username})

    def test_home(self):
        '''
        The home page should return HTTP code 200 OK
        '''
        response = self.client.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_new_user(self):
        '''
        The new-user page should return 200
        '''
        response = self.client.get('/new-user', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_create_new_user(self):
        '''
        Creating a new-user should return 200
        '''
        response = self.client.post('/new-user', follow_redirects=True,
                                    data={'username': 'TestUser'})
        self.assertEqual(response.status_code, 200)

    def test_create_new_user_adds_user(self):
        '''
        Creating a new user should add them to the logins collection
        '''
        username = 'TestUser'
        self.create_user(username)
        self.assertNotEqual(self.mongo.db.logins.find_one({'username': username}), None)

    def test_create_new_user_already_exists(self):
        '''
        Trying to create a new user that already exists should fail
        '''
        username = 'TestUser'
        self.create_user(username)
        self.create_user(username)
        self.assertEqual(self.mongo.db.logins.count_documents({'username': username}), 1)

    def test_create_new_user_missing_username(self):
        '''
        Trying to create a user with a blank username should fail
        '''
        username = ''
        self.create_user(username)
        self.assertEqual(self.mongo.db.logins.find_one({'username': username}), None)

        username = None
        self.create_user(username)
        self.assertEqual(self.mongo.db.logins.find_one({'username': username}), None)

    def test_create_new_user_invalid_username(self):
        '''
        Trying to create a user with username containing anything other than alphanumeric characters should fail
        '''
        username = ':D 8p >/'
        self.create_user(username)
        self.assertEqual(self.mongo.db.logins.find_one({'username': username}), None)


if __name__ == '__main__':
    unittest.main()

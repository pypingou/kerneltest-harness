# Licensed under the terms of the GNU GPL License version 2

'''
kerneltest tests.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import json
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import kerneltest.app as app
import kerneltest.dbtools as dbtools
from tests import Modeltests, user_set, FakeFasUser


class KerneltestTests(Modeltests):
    """ kerneltest tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(KerneltestTests, self).setUp()

        app.APP.config['TESTING'] = True
        app.SESSION = self.session
        self.app = app.APP.test_client()

    def test_upload_results_loggedin(self):
        ''' Test the app.upload_results function. '''
        folder = os.path.dirname(os.path.abspath(__file__))
        filename = '1.log'
        full_path = os.path.join(folder, filename)

        user = FakeFasUser()
        with user_set(app.APP, user):
            output = self.app.get('/upload/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<td><input id="test_result" name="test_result" '
                'type="file"></td>' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # Valid upload via the UI
            stream = open(full_path)
            data = {
                'test_result': stream,
                'username': 'pingou',
                'csrf_token': csrf_token,
            }
            output = self.app.post('/upload/', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Upload successful!</li>' in output.data)

            # Valid upload authenticated and via the anonymous API
            stream = open(full_path)
            data = {
                'test_result': stream,
                'username': 'pingou',
            }
            output = self.app.post('/upload/anonymous', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(data, {'message': 'Upload successful!'})

            # Invalid file upload
            full_path = os.path.join(folder, 'invalid.log')
            stream = open(full_path)
            data = {
                'test_result': stream,
                'username': 'pingou',
                'csrf_token': csrf_token,
            }
            output = self.app.post('/upload/', data=data)
            self.assertEqual(output.status_code, 302)

            # Invalid file upload
            full_path = os.path.join(folder, 'invalid.log')
            stream = open(full_path)
            data = {
                'test_result': stream,
                'username': 'pingou',
                'csrf_token': csrf_token,
            }
            output = self.app.post('/upload/', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Could not parse these results</li>'
                in output.data)

        # Invalid username
        user = FakeFasUser()
        user.username = 'kerneltest'
        with user_set(app.APP, user):
            full_path = os.path.join(folder, 'invalid.log')
            stream = open(full_path)
            data = {
                'test_result': stream,
                'username': 'pingou',
                'csrf_token': csrf_token,
            }
            output = self.app.post('/upload/', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">The `kerneltest` username is reserved, '
                'you are not allowed to use it</li>' in output.data)

    def test_upload_results_anonymous(self):
        ''' Test the app.upload_results function for an anonymous user. '''
        folder = os.path.dirname(os.path.abspath(__file__))
        filename = '2.log'

        user = None
        with user_set(app.APP, user):
            output = self.app.get('/upload/')
            self.assertEqual(output.status_code, 302)
            self.assertTrue('<title>Redirecting...</title>' in output.data)

        user = None
        with user_set(app.APP, user):
            output = self.app.get('/upload/anonymous')
            self.assertEqual(output.status_code, 405)
            self.assertTrue(
                '<title>405 Method Not Allowed</title>' in output.data)

            full_path = os.path.join(folder, filename)
            stream = open(full_path)
            data = {
                'test_result': stream,
                'username': 'pingou',
            }
            output = self.app.post('/upload/', data=data)
            self.assertEqual(output.status_code, 302)
            self.assertTrue('<title>Redirecting...</title>' in output.data)

            # Invalid request
            data = {
                'username': 'pingou',
            }
            output = self.app.post('/upload/anonymous', data=data)
            self.assertEqual(output.status_code, 400)
            data = json.loads(output.data)
            exp = {
                "error": "Invalid request",
                "messages": {
                    "test_result": [
                        "This field is required."
                    ]
                }
            }
            self.assertEqual(data, exp)

            # Invalid username

            stream = open(full_path)
            data = {
                'test_result': stream,
                'username': 'kerneltest',
            }
            output = self.app.post('/upload/anonymous', data=data)
            self.assertEqual(output.status_code, 401)
            data = json.loads(output.data)
            exp = {
                'error': 'The `kerneltest` username is reserved, you are '
                'not allowed to use it'
            }
            self.assertEqual(data, exp)

            # Valid and successful upload
            stream = open(full_path)
            data = {
                'test_result': stream,
                'username': 'pingou',
            }
            output = self.app.post('/upload/anonymous', data=data)
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.data)
            self.assertEqual(data, {'message': 'Upload successful!'})

            # Invalid file upload
            full_path = os.path.join(folder, 'invalid.log')
            stream = open(full_path)
            data = {
                'test_result': stream,
                'username': 'ano',
            }
            output = self.app.post('/upload/anonymous', data=data)
            self.assertEqual(output.status_code, 400)
            data = json.loads(output.data)
            exp = {"error": "Invalid input file"}
            self.assertEqual(data, exp)

            # Invalid mime type uploaded
            full_path = os.path.join(folder, 'denied.png')
            stream = open(full_path)
            data = {
                'test_result': stream,
                'username': 'ano',
            }
            output = self.app.post('/upload/anonymous', data=data)
            self.assertEqual(output.status_code, 400)
            data = json.loads(output.data)
            exp = {"error": "Invalid input file"}
            self.assertEqual(data, exp)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(KerneltestTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)

import unittest
from tornado import httpclient
import simplejson as json

class TestAuth(unittest.TestCase):
    def setUp(self):
        self.http_client = httpclient.HTTPClient()
        self.url_head = "http://localhost/authapi/"

    # register
    def test_register(self):
        response = self.http_client.fetch(self.url_head+"register?username=aa&password=aa")
        response = json.loads(response.body)
        self.assertIn(response["error"], (0, "err_exist"))

    def test_register_param_error(self):
        def test_param(param):
            response = self.http_client.fetch(self.url_head+"register?"+param)
            response = json.loads(response.body)
            self.assertEqual(response["error"], "err_param")
        params = [
            "username=aa",
            "username=aa&password=",
            "",
            "username=;&password=aa"
            "username=&&password=aa"
        ]
        map(test_param, params)

    # login
    def test_login(self):
        response = self.http_client.fetch(self.url_head+"login?username=aa&password=aa")
        response = json.loads(response.body)
        self.assertEqual(response["error"], 0)
        self.assertTrue("usertoken" in response)

    def test_login_wrong_password(self):
        response = self.http_client.fetch(self.url_head+"login?username=aa&password=sdfkjasdi")
        response = json.loads(response.body)
        self.assertEqual(response["error"], "err_not_match")

    def test_login_user_not_exist(self):
        response = self.http_client.fetch(self.url_head+"login?username=kjisdfji&password=sdfkjasdi")
        response = json.loads(response.body)
        self.assertEqual(response["error"], "err_not_match")

if __name__ == '__main__':
    unittest.main()
import unittest
from tornado import httpclient
import simplejson as json

class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.http_client = httpclient.HTTPClient()
        self.url_head = "http://localhost/whapi/player/"

    # getinfo
    def test_getinfo(self):
        response = self.http_client.fetch(self.url_head+"getinfo")
        response = json.loads(response.body)
        self.assertIn(response["error"], (0, "err_exist"))

if __name__ == '__main__':
    unittest.main()
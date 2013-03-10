from test import auth_test
import unittest

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromModule(auth_test)
    unittest.TextTestRunner().run(suite)
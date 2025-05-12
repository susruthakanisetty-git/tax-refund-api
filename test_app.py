import unittest
import json
from app import app  # Import your Flask app

class TestRefundAPI(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_valid_pin(self):
        #  Mock the external API call 
        import requests
        def mock_get(*args, **kwargs):
            class MockResponse:
                def __init__(self, json_data, status_code):
                    self.json_data = json_data
                    self.status_code = status_code

                def json(self):
                    return self.json_data

                def raise_for_status(self):
                    if self.status_code >= 400:
                        raise requests.exceptions.HTTPError("Error")

            #  Example mock response 
            mock_response_data = {
                "1011230070000": {
                    "assessed value": 250000,
                    "sale date": "1/15/2020"
                },
                "comparable1": {"assessed value": 200000},
                "comparable2": {"assessed value": 220000}
            }
            return MockResponse(mock_response_data, 200)

        requests.get = mock_get  

        response = self.app.post('/refund', json={'pin': '1011230070000'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('totalRefund', data)

    def test_invalid_pin(self):
        response = self.app.post('/refund', json={'pin': 'invalid'})
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main()
import unittest
from unittest.mock import patch, MagicMock
from stocks.controller import StockController
SINGLE_MOCK_STOCKS = [
    {
        "_id": "1",
        "name": "Apple Inc.",
        "symbol": "AAPL",
        "purchase price": 150.0,
        "purchase date": "01-10-2023",
        "shares": 10
    }]

DOUBLE_MOCK_STOCKS = [
    {
        "_id": "1",
        "name": "Apple Inc.",
        "symbol": "AAPL",
        "purchase price": 150.0,
        "purchase date": "01-10-2023",
        "shares": 10
    },
    {
        "_id": "2",
        "name": "Microsoft Corp.",
        "symbol": "MSFT",
        "purchase price": 300.0,
        "purchase date": "01-11-2023",
        "shares": 20
    }
]


class TestController(unittest.TestCase):
    def setUp(self):
        self.mock_stocks_collection = MagicMock()  # Mock the MongoDB collection
        self.controller_service = StockController(self.mock_stocks_collection)
        self.client = self.controller_service.app.test_client()

    @patch('service.StockService.symbol_exists')  # Patch the symbol_exists method
    def test_add_valid_stock(self, mock_symbol_exists):
        mock_symbol_exists.return_value = False  # Mock symbol_exists to return False
        self.mock_stocks_collection.insert_one.return_value.inserted_id = "stock123"

        # Define test cases
        cases = [
            {
                "description": "Complete payload, expecting 201",
                "payload": {
                    "symbol": "AAPL",
                    "purchase price": 150.0,
                    "shares": 10,
                    "name": "Apple Inc.",
                    "purchase date": "01-10-2023"}
            }
            ,
            {
                "description": "Partial payload, expecting 201",
                "payload": {
                    "symbol": "AAPL",
                    "purchase price": 150.0,
                    "shares": 10}
            }
        ]

        # Run each test case
        for case in cases:
            with self.subTest(case=case["description"]):
                self.setUp()
                # Perform the POST request
                response = self.client.post(
                    '/stocks',
                    json=case["payload"],
                    content_type='application/json'
                )

                # Assert the response status and content
                self.assertEqual(response.status_code, 201)
                self.assertIn("id", response.json)

    @patch('service.StockService.symbol_exists')  # Patch the symbol_exists method
    def test_add_invalid_stock(self, mock_symbol_exists):
        mock_symbol_exists.return_value = False

        # Define invalid test cases
        cases = [
            {
                "description": "Missing required field 'symbol'",
                "payload": {
                    "purchase price": 150.0,
                    "shares": 10
                },
                "expected_status": 400,
                "expected_error": "Malformed data",
            },
            {
                "description": "Negative 'purchase price'",
                "payload": {
                    "symbol": "AAPL",
                    "purchase price": -150.0,
                    "shares": 10
                },
                "expected_status": 400,
                "expected_error": "Malformed data",
            },
            {
                "description": "Zero 'shares'",
                "payload": {
                    "symbol": "AAPL",
                    "purchase price": 150.0,
                    "shares": 0
                },
                "expected_status": 400,
                "expected_error": "Malformed data",
            },
            {
                "description": "Invalid content type (not JSON)",
                "payload": "Invalid payload",
                "expected_status": 415,
                "expected_error": "Expected application/json media type",
                "content_type": "text/plain"
            }
        ]

        # Run each invalid case
        for case in cases:
            with self.subTest(case=case["description"]):
                # Determine content type
                content_type = case.get("content_type", "application/json")

                # Perform the POST request
                response = self.client.post(
                    '/stocks',
                    json=case["payload"] if content_type == "application/json" else None,
                    data=case["payload"] if content_type != "application/json" else None,
                    content_type=content_type
                )

                # Assert the response
                self.assertEqual(response.status_code, case["expected_status"])
                self.assertIn("error", response.json)
                self.assertEqual(response.json["error"], case["expected_error"])

    # def test_duplicate_stock_symbol(self):
    #     payloads = [
    #         {
    #             "symbol": "AAPL",
    #             "purchase price": 150.0,
    #             "shares": 10,
    #             "name": "Apple Inc.",
    #             "purchase date": "01-10-2023"
    #         },{
    #             "symbol": "AAPL",
    #             "purchase price": 160.0,
    #             "shares": 50,
    #             "name": "Apple Inc.",
    #             "purchase date": "01-10-2023"
    #         }]
    #
    #     # Add the first stock
    #     response = self.client.post(
    #         '/stocks',
    #         json=payloads[0],
    #         content_type='application/json'
    #     )
    #
    #     # Assert the first addition is successful
    #     self.assertEqual(response.status_code, 201)
    #     self.assertIn("id", response.json)
    #
    #     # Add the second stock with the same symbol
    #     response = self.client.post(
    #         '/stocks',
    #         json=payloads[1],
    #         content_type='application/json'
    #     )
    #
    #     # Assert the second addition fails due to duplication
    #     self.assertEqual(response.status_code, 400)
    #     self.assertIn("error", response.json)
    #     self.assertEqual(response.json["error"], "Malformed data")

    # @patch('service.StockService.symbol_exists')  # Patch symbol_exists
    # def test_get_stocks(self, mock_symbol_exists):
    #     """
    #     Test retrieving stocks with MongoDB mock.
    #     """
    #     mock_symbol_exists.return_value = False
    #     self.mock_stocks_collection.find.return_value = DOUBLE_MOCK_STOCKS
    #
    #     # Test cases
    #     cases = [
    #         {
    #             "description": "Get all stocks, expect 200",
    #             "query_params": "",
    #             "expected_response": DOUBLE_MOCK_STOCKS
    #
    #         },
    #         {
    #             "description": "Filter stocks by symbol (AAPL), expect 200",
    #             "query_params": "?symbol=AAPL",
    #             "expected_response": SINGLE_MOCK_STOCKS
    #         },
    #         {
    #             "description": "Filter stocks by non-existent symbol, expect 200 with empty list",
    #             "query_params": "?symbol=GOOGL",
    #             "expected_response": []
    #         }
    #     ]
    #
    #     for case in cases:
    #         with self.subTest(case=case["description"]):
    #             # Perform the GET request with query parameters
    #             response = self.client.get(f'/stocks{case["query_params"]}')
    #
    #             # Assert the response
    #             self.assertEqual(response.status_code, 200)
    #             self.assertEqual(response.json, case["expected_response"])

    # def test_get_stock(self):
    #     # Create a real stock and an in-memory portfolio
    #     stock = Stock("1", "Apple Inc.", "AAPL", 150.0, "01-10-2023", 10)
    #     portfolio = {"1": stock}  # Directly define the portfolio
    #
    #     # Assign the portfolio to the controller's StockService
    #     self.controller_service.stock_service.portfolio = portfolio
    #
    #     # Test cases
    #     cases = [
    #         {
    #             "description": "Valid stock ID, expect 200",
    #             "stock_id": "1",
    #             "expected_status": 200,
    #             "expected_response": stock.__dict__,
    #         },
    #         {
    #             "description": "Non-existent stock ID, expect 404",
    #             "stock_id": "nonexistent",
    #             "expected_status": 404,
    #             "expected_response": {"error": "Not found"},
    #         }
    #     ]
    #
    #     # Run the test cases
    #     for case in cases:
    #         with self.subTest(case=case["description"]):
    #             # Perform the GET request
    #             response = self.client.get(f'/stocks/{case["stock_id"]}')
    #
    #             # Assert the response
    #             self.assertEqual(response.status_code, case["expected_status"])
    #             self.assertEqual(response.json, case["expected_response"])

    # def test_remove_stock(self):
    #     # Set up the StockService and populate it with test data
    #     self.controller_service.stock_service.portfolio = {
    #         "1": Stock("1", "Apple Inc.", "AAPL", 150.0, "01-10-2023", 10),
    #         "2": Stock("2", "Microsoft Corp.", "MSFT", 300.0, "01-11-2023", 20),
    #     }
    #
    #     # Test cases
    #     cases = [
    #         {
    #             "description": "Remove an existing stock, expect 204",
    #             "stock_id": "1",
    #             "expected_status": 204,
    #             "expected_response": None  # No content for 204 status
    #         },
    #         {
    #             "description": "Remove a non-existent stock, expect 404",
    #             "stock_id": "3",
    #             "expected_status": 404,
    #             "expected_response": {"error": "Not found"}
    #         }
    #     ]
    #
    #     for case in cases:
    #         with self.subTest(case=case["description"]):
    #             # Perform the DELETE request
    #             response = self.client.delete(f'/stock/{case["stock_id"]}')
    #
    #             # Assert the response status code
    #             self.assertEqual(response.status_code, case["expected_status"])
    #
    #             # Assert the response body (if any)
    #             if case["expected_response"] is not None:
    #                 self.assertEqual(response.json, case["expected_response"])
    #
    #     # Verify that the stock was removed from the portfolio
    #     self.assertNotIn("1", self.controller_service.stock_service.portfolio)
    #
    # def test_update_stock(self):
    #     # Set up the StockService with initial stock data
    #     self.controller_service.stock_service.portfolio = INITIAL_PORTFOLIO_SINGLE
    #
    #     # Valid payload for updating the stock
    #     valid_payload = {
    #         "id": "1",
    #         "symbol": "AAPL",
    #         "name": "Updated Apple Inc.",
    #         "purchase price": 200.0,
    #         "purchase date": "01-12-2023",
    #         "shares": 20
    #     }
    #
    #     # Perform the PUT request
    #     response = self.client.put(
    #         '/stocks/1',
    #         json=valid_payload,
    #         content_type='application/json'
    #     )
    #
    #     # Assert the response for successful update
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.json, {"id": "1"})
    #
    #     # Verify the stock is updated in the portfolio
    #     updated_stock = self.controller_service.stock_service.portfolio["1"]
    #     self.assertEqual(updated_stock.name, "Updated Apple Inc.")
    #     self.assertEqual(updated_stock.purchase price, 200.0)
    #     self.assertEqual(updated_stock.shares, 20)
    #
    # def test_update_stock_bad_cases(self):
    #     # Test cases for bad requests
    #     cases = [
    #         {
    #             "description": "Invalid content type, expect 415",
    #             "stock_id": "1",
    #             "payload": {
    #                 "id": "1",
    #                 "symbol": "AAPL",
    #                 "name": "Updated Apple Inc.",
    #                 "purchase price": 200.0,
    #                 "purchase date": "01-12-2023",
    #                 "shares": 20
    #             },
    #             "content_type": "text/plain",
    #             "expected_status": 415,
    #             "expected_response": {"error": "Expected application/json media type"}
    #         },
    #         {
    #             "description": "Missing required fields, expect 400",
    #             "stock_id": "1",
    #             "payload": {
    #                 "id": "1",
    #                 "symbol": "AAPL",
    #                 # Missing 'name', 'purchase price', 'purchase date', 'shares'
    #             },
    #             "content_type": "application/json",
    #             "expected_status": 400,
    #             "expected_response": {"error": "Malformed data"}
    #         },
    #         {
    #             "description": "ID mismatch, expect 400",
    #             "stock_id": "2",  # URL stock_id doesn't match payload ID
    #             "payload": {
    #                 "id": "1",
    #                 "symbol": "AAPL",
    #                 "name": "Updated Apple Inc.",
    #                 "purchase price": 200.0,
    #                 "purchase date": "01-12-2023",
    #                 "shares": 20
    #             },
    #             "content_type": "application/json",
    #             "expected_status": 400,
    #             "expected_response": {"error": "ID mismatch"}
    #         },
    #         {
    #             "description": "Invalid purchase price, expect 400",
    #             "stock_id": "1",
    #             "payload": {
    #                 "id": "1",
    #                 "symbol": "AAPL",
    #                 "name": "Updated Apple Inc.",
    #                 "purchase price": -200.0,  # Invalid negative price
    #                 "purchase date": "01-12-2023",
    #                 "shares": 20
    #             },
    #             "content_type": "application/json",
    #             "expected_status": 400,
    #             "expected_response": {"error": "Invalid data"}
    #         },
    #         {
    #             "description": "Invalid number of shares, expect 400",
    #             "stock_id": "1",
    #             "payload": {
    #                 "id": "1",
    #                 "symbol": "AAPL",
    #                 "name": "Updated Apple Inc.",
    #                 "purchase price": 200.0,
    #                 "purchase date": "01-12-2023",
    #                 "shares": -10  # Invalid negative shares
    #             },
    #             "content_type": "application/json",
    #             "expected_status": 400,
    #             "expected_response": {"error": "Invalid data"}
    #         }
    #     ]
    #
    #     # Run the test cases
    #     for case in cases:
    #         with self.subTest(case=case["description"]):
    #             # Ensure setup is called for each subtest
    #             self.setUp()
    #             self.controller_service.stock_service.portfolio = INITIAL_PORTFOLIO_SINGLE
    #
    #             # Perform the PUT request
    #             response = self.client.put(
    #                 f'/stocks/{case["stock_id"]}',
    #                 json=case.get("payload") if case["content_type"] == "application/json" else None,
    #                 data=case.get("payload") if case["content_type"] != "application/json" else None,
    #                 content_type=case["content_type"]
    #             )
    #
    #             # Assert the response status and body
    #             self.assertEqual(response.status_code, case["expected_status"])
    #             self.assertEqual(response.json, case["expected_response"])
    #
    # @patch('service.StockService.fetch_stock_current_price')
    # def test_stock_value(self, mock_fetch_price):
    #     # Define test cases
    #     cases = [
    #         {
    #             "description": "Valid stock ID, expect 200",
    #             "stock_id": "1",
    #             "mock_price": 200.0,  # Mocked current price
    #             "expected_status": 200,
    #             "expected_response": {
    #                 "symbol": "AAPL",
    #                 "ticker": 200.0,
    #                 "stock value": 2000.0
    #             }
    #         },
    #         {
    #             "description": "Non-existent stock ID, expect 404",
    #             "stock_id": "999",
    #             "mock_price": None,  # No price fetching needed
    #             "expected_status": 404,
    #             "expected_response": {"error": "Not found"}
    #         }
    #     ]
    #
    #     for case in cases:
    #         with self.subTest(case=case["description"]):
    #             self.setUp()
    #             self.controller_service.stock_service.portfolio = INITIAL_PORTFOLIO_SINGLE
    #
    #             # Set up the mock price if applicable
    #             if case["mock_price"] is not None:
    #                 mock_fetch_price.return_value = case["mock_price"]
    #
    #             # Perform the GET request
    #             response = self.controller_service.app.test_client().get(f'/stock-value/{case["stock_id"]}')
    #
    #             # Assert the response status code
    #             self.assertEqual(response.status_code, case["expected_status"])
    #
    #             # Assert the response data
    #             if case["expected_status"] == 200:
    #                 self.assertEqual(response.json, case["expected_response"])
    #             else:
    #                 self.assertEqual(response.json, case["expected_response"])
    #
    # @patch('service.StockService.fetch_stock_current_price')
    # def test_portfolio_value(self, mock_fetch_price):
    #     self.controller_service.stock_service.portfolio = INITIAL_PORTFOLIO_DOUBLE
    #
    #     # Mock current prices for the stocks
    #     mock_prices = {
    #         "AAPL": 200.0,
    #         "MSFT": 250.0
    #     }
    #
    #     def fetch_price_side_effect(symbol):
    #         return mock_prices[symbol]
    #
    #     # Set the side effect for fetch_stock_current_price
    #     mock_fetch_price.side_effect = fetch_price_side_effect
    #
    #     # Perform the GET request for portfolio value
    #     response = self.controller_service.app.test_client().get('/portfolio-value')
    #
    #     # Calculate the expected total portfolio value
    #     expected_total_value = (10 * mock_prices["AAPL"]) + (20 * mock_prices["MSFT"])
    #
    #     # Assert the response
    #     self.assertEqual(response.status_code, 200)
    #     self.assertIn("portfolio value", response.json)
    #     self.assertEqual(response.json["portfolio value"], expected_total_value)


if __name__ == '__main__':
    unittest.main()
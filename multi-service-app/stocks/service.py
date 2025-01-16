import logging
import time
import requests
from requests import RequestException
from bson import ObjectId

NINJA_API_KEY = "t7kGKURsW31xlUX9jhmX6Q==JKxHUYND1othy0fC"
API_URL = 'https://api.api-ninjas.com/v1/stockprice?ticker={}'


class StockService:
    def __init__(self, stocks_collection):
        self.stocks_collection = stocks_collection

    def add_stock(self, symbol: str, purchase_price: float, shares: int,
                  name: str = 'NA', purchase_date: str = 'NA') -> dict:
        """
         Inserts a new stock into the MongoDB collection.
         """
        new_stock = {
            "name": name,
            "symbol": symbol,
            "purchase price": round(purchase_price, 2),
            "purchase date": purchase_date,
            "shares": shares
        }
        result = self.stocks_collection.insert_one(new_stock)
        return self.stocks_collection.find_one({"_id": result.inserted_id})

    def get_stock_by_id(self, stock_id: str) -> dict:
        try:
            stock = self.stocks_collection.find_one({"_id": self.convert_to_object_id(stock_id)})
            if not stock:
                raise KeyError(f"Stock with id '{stock_id}' not found in the portfolio.")
            return stock
        except Exception as e:
            raise KeyError(f"Stock with id '{stock_id}' not found. Ensure the ID is correct: {e}.")

    def delete_stock(self, stock_id: str) -> int:
        """
         Deletes a stock by its ID.
         Returns: The number of documents deleted (0 or 1).
         """
        try:
            result = self.stocks_collection.delete_one({"_id": self.convert_to_object_id(stock_id)})
            return result.deleted_count
        except Exception as e:
            raise KeyError(f"Error deleting stock with id '{stock_id}': {e}")

    def update_stock(self, stock_id: str, updated_data: dict) -> int:
        """
        Updates a stock's fields by its ID.
        Returns: The number of documents updated (0 or 1).
        """
        try:
            result = self.stocks_collection.update_one(
                {"_id": self.convert_to_object_id(stock_id)},
                {"$set": updated_data}
            )
            # Check if any document was modified
            if result.matched_count == 0:
                return -1  # Stock not found
            return result.modified_count  # 0 if unchanged, 1 if updated
        except Exception as e:
            raise KeyError(f"Stock with id '{stock_id}' not found. Ensure the ID is correct: {e}.")

    @staticmethod
    def fetch_stock_current_price(symbol: str, retries=3, delay=2) -> float:
        """
        For more info: https://api-ninjas.com/api/stockprice
        """
        for attempt in range(retries):
            try:
                # Ensure the symbol is valid and properly formatted
                symbol = symbol.strip().upper()
                response = requests.get(API_URL.format(symbol), headers={'X-Api-Key': NINJA_API_KEY}, timeout=10)

                if response.status_code == requests.codes.ok:
                    response_json = response.json()
                    if 'price' in response_json:
                        return response_json['price']
                    else:
                        # Treat empty or unexpected responses as invalid symbols
                        raise ValueError(f"Invalid stock symbol: {symbol}")
                else:
                    raise ValueError(f"Unexpected status code: {response.status_code}")

            except RequestException as e:
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    raise ValueError(f"API request failed after {retries} attempts: {str(e)}")

    def get_stock_value(self, stock_id: str) -> dict:
        try:
            stock = self.get_stock_by_id(stock_id)
        except KeyError:
            raise KeyError(f"Stock with ID '{stock_id}' not found.")
        try:
            current_price = round(self.fetch_stock_current_price(stock['symbol']), 2)
            stock_value = round(stock['shares'] * current_price, 2)

            # Return the required data as a dictionary
            return {
                "symbol": stock['symbol'],
                "ticker": current_price,
                "stock_value": stock_value
            }
        except Exception as e:
            raise ValueError(f"Error fetching stock value for '{stock['symbol']}': {str(e)}")

    def get_stocks(self, query_params) -> list[dict]:
        """
        Retrieves all stocks from the database.
        Returns: A list of stock objects represented as dictionaries.
        """
        # return list(self.stocks_collection.find())
        try:
            if query_params:
                numeric_fields = ['purchase price', 'shares']  # Define numeric fields here
                query_params = self.convert_query_params(query_params, numeric_fields)

            return list(self.stocks_collection.find(query_params or {}))

        except Exception as e:
            logging.error(f"Error fetching stocks: {str(e)}")
            raise

    def get_portfolio_value(self) -> float:
        total_value = 0.0
        try:
            for stock in self.stocks_collection.find():
                current_price = self.fetch_stock_current_price(stock['symbol'])
                if current_price:
                    total_value += stock['shares'] * current_price
                else:
                    raise ValueError(f"Price for stock '{stock['symbol']}' (id: {stock['_id']}) "
                                     f"is not available. Please update the symbol.")

            return round(total_value, 2)
        except Exception as e:
            raise ValueError(f"Error calculating portfolio value: {str(e)}")

    @staticmethod
    def convert_query_params(query_params, numeric_fields):
        """
        Helper function to convert specific query parameters to numeric types.
        """
        for key, value in query_params.items():
            if key in numeric_fields:
                try:
                    query_params[key] = float(value)  # Convert to float for numeric matching
                except ValueError:
                    # Log and ignore conversion errors, or handle as needed
                    logging.warning(f"Failed to convert {key}='{value}' to a numeric value.")
                    raise ValueError(f"Invalid value for field '{key}'. Expected a numeric value.")
        return query_params

    def symbol_exists(self, symbol: str) -> bool:
        return self.stocks_collection.find_one({"symbol": symbol}) is not None

    def stock_id_exists(self, stock_id: str) -> bool:
        try:
            return self.stocks_collection.find_one({"_id": ObjectId(stock_id)}) is not None
        except Exception:
            return False

    @staticmethod
    def convert_to_object_id(stock_id: str) -> ObjectId:
        try:
            return ObjectId(stock_id)
        except Exception:
            raise ValueError(f"Invalid stock ID format: '{stock_id}'")

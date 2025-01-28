import logging
import os
import time
from datetime import datetime
from flask import Flask, request, jsonify
from service import StockService
from DistributedLock import DistributedLock


class StockController:
    def __init__(self, stocks_collection, locks_delete_update_collection, locks_add_collection):
        self.app = Flask(__name__)
        self.stock_service = StockService(stocks_collection)
        self.setup_routes()
        self.locks_delete_update = DistributedLock(locks_delete_update_collection)
        self.locks_add = DistributedLock(locks_add_collection)

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def setup_routes(self):
        # Define the routes and bind them to class methods
        self.app.route('/stocks', methods=['POST'])(self.add_stock)
        self.app.route('/stocks', methods=['GET'])(self.get_stocks)
        self.app.route('/stocks/<string:stock_id>', methods=['GET'])(self.get_stock)
        self.app.route('/stocks/<string:stock_id>', methods=['DELETE'])(self.remove_stock)
        self.app.route('/stocks/<string:stock_id>', methods=['PUT'])(self.update_stock)
        self.app.route('/stock-value/<string:stock_id>', methods=['GET'])(self.stock_value)
        self.app.route('/portfolio-value', methods=['GET'])(self.portfolio_value)
        self.app.route('/kill', methods=['GET'])(self.kill_container)

    def validate_stock_data(self, data, required_fields, check_symbol_exists):
        for field in required_fields:
            # Check if the field exists and is not empty
            if field not in data or not str(data[field]).strip():
                logging.error(f"Validation failed: '{field}' is missing or empty.")
                return False

        if check_symbol_exists and self.stock_service.symbol_exists(data['symbol']):
            logging.error(f"Validation failed: Stock with symbol '{data['symbol']}' already exists.")
            return False

        if not self.validate_symbol(data['symbol']):
            return False

        if not self.validate_purchase_price(data['purchase price']):
            return False

        if not self.validate_number_of_shares(data['shares']):
            return False

        logging.info("Stock data validation passed.")
        return True

    @staticmethod
    def validate_purchase_price(purchase_price):
        try:
            if float(purchase_price) <= 0:
                logging.error("Validation failed: 'purchase price' must be a positive number.")
                return False
        except (ValueError, TypeError):
            logging.error("Validation failed: 'purchase price' must be a valid number.")
            return False
        return True

    @staticmethod
    def validate_number_of_shares(number_of_shares):
        try:
            if int(number_of_shares) <= 0:
                logging.error("Validation failed: 'shares' must be a positive integer.")
                return False
        except (ValueError, TypeError):
            logging.error("Validation failed: 'shares' must be a valid integer.")
            return False
        return True

    @staticmethod
    def validate_symbol(symbol):
        # Validate 'symbol': must be a non-empty uppercase string
        if isinstance(symbol, str) and symbol.isupper():
            return True
        logging.error("Validation failed: 'symbol' must be an uppercase string.")
        return False

    def add_stock(self):
        """
        POST: The POST request provides a JSON object payload that must contain: 'symbol', 'purchase price',
        'shares' fields. Optionally it can also provide the ‘name’ and 'purchase date' of the stock. If successful,
        it returns the JSON for the id * assigned to that object with status code 201. Possible error status codes
        returned: 400, 415, 500.
        """
        try:
            content_type = request.headers.get('Content-Type')
            if content_type != 'application/json':
                return jsonify({'error': 'Expected application/json media type'}), 415
            data = request.get_json()

        except Exception as e:
            return jsonify({'server error': str(e)}), 500

        if not self.acquire_lock_with_retries(self.locks_add, data['symbol']):
            return jsonify({"error": "Resource is locked by another operation."}), 409

        try:
            if not self.validate_stock_data(data, ['symbol', 'purchase price', 'shares'], check_symbol_exists=True):
                return jsonify({'error': 'Malformed data'}), 400

            name = data.get('name', 'NA')
            symbol = data['symbol']
            purchase_price = data['purchase price']
            purchase_date = data.get('purchase date', 'NA')
            shares = data['shares']

            # note: id is generated in the service layer
            stock = self.stock_service.add_stock(symbol, purchase_price, shares, name, purchase_date)
            stock['id'] = str(stock.pop('_id'))  # Use 'id' for external response

            return jsonify(stock), 201
        except Exception as e:
            return jsonify({'server error': str(e)}), 500

        finally:
            self.locks_add.release_lock(data['symbol'])
            logging.info(f"Lock released for stock '{data['symbol']}'.")

    def get_stocks(self):
        """
        GET: If successful, it returns a JSON array of stock objects with status code 200.
        Possible error status codes returned: 500.
        For this assignment, you need to support query strings of the form <field>=<value>.
        """
        try:
            query_params = request.args.to_dict()
            stocks = self.stock_service.get_stocks(query_params)

            # Convert ObjectId to string for JSON serialization
            for stock in stocks:
                stock['id'] = str(stock.pop('_id'))

            return jsonify(stocks), 200

        except Exception as e:
            logging.error(f"Error in get_stocks: {str(e)}")
            return jsonify({'server error': str(e)}), 500

    def get_stock(self, stock_id):
        try:
            stock = self.stock_service.get_stock_by_id(stock_id)
            stock['id'] = str(stock.pop('_id'))
            return jsonify(stock), 200
        except KeyError:
            logging.error(f"DELETE request error: Stock with id '{stock_id}' not found.")
            return jsonify({"error": "Not found"}), 404
        except Exception as e:
            return jsonify({'server error': str(e)}), 500

    def remove_stock(self, stock_id):
        if not self.acquire_lock_with_retries(self.locks_delete_update, stock_id):
            return jsonify({"error": "Resource is locked by another operation."}), 409

        try:
            self.stock_service.delete_stock(stock_id)
            return '', 204
        except KeyError:
            logging.error(f"DELETE request error: Stock with id '{stock_id}' not found.")
            return jsonify({"error": "Not found"}), 404
        except Exception as e:
            logging.error(f"Error in remove_stock: {str(e)}")
            return jsonify({'server error': str(e)}), 500

        finally:
            self.locks_delete_update.release_lock(stock_id)
            logging.info(f"Lock released for stock '{stock_id}'.")

    def update_stock(self, stock_id):
        if not self.acquire_lock_with_retries(self.locks_delete_update, stock_id):
            return jsonify({"error": "Resource is locked by another operation."}), 409

        try:
            content_type = request.headers.get('Content-Type')
            if content_type != 'application/json':
                return jsonify({"error": "Expected application/json media type"}), 415

            data = request.get_json()
            required_fields = ['id', 'symbol', 'name', 'purchase price', 'purchase date', 'shares']

            if not self.validate_stock_data(data, required_fields, check_symbol_exists=False):
                return jsonify({'error': 'Malformed data'}), 400

            # Ensure the ID in the payload matches the stock_id in the URL
            if data['id'] != stock_id:
                logging.error(
                    f"Validation failed: Stock ID in URL '{stock_id}' does not match ID in payload '{data['id']}'.")
                return jsonify({"error": "ID mismatch"}), 400

            # Update stock in the service layer
            update_result = self.stock_service.update_stock(
                stock_id,
                {
                    'symbol': data['symbol'],
                    'name': data['name'],
                    'purchase price': float(data['purchase price']),
                    'purchase date': data['purchase date'],
                    'shares': int(data['shares'])
                }
            )

            if update_result == -1:
                logging.error(f"PUT error: Stock with ID '{stock_id}' not found.")
                return jsonify({"error": "Not found"}), 404
            elif update_result == 0:
                logging.info(f"No changes made for stock with ID '{stock_id}'.")
                return jsonify({"message": "No changes made"}), 200  # Or use 204 No Content
            else:
                response_data = {"id": stock_id}
                return jsonify(response_data), 200

        except Exception as e:
            logging.error(f"Exception in update_stock: {str(e)}")
            return jsonify({"server error": str(e)}), 500

        finally:
            self.locks_delete_update.release_lock(stock_id)
            logging.info(f"Lock released for stock '{stock_id}'.")

    def stock_value(self, stock_id):
        """
        GET: Returns the current value of a stock with the given ID.
        """
        try:
            stock_value_data = self.stock_service.get_stock_value(stock_id)
            return jsonify(stock_value_data), 200

        except KeyError:
            logging.error(f"Stock with ID '{stock_id}' not found.")
            return jsonify({"error": "Not found"}), 404

        except ValueError as e:
            stock = self.stock_service.get_stock_by_id(stock_id)
            stock_symbol = stock["symbol"] if stock else "Unknown"

            logging.error(f"Invalid stock symbol '{stock_symbol}' (ID: {stock_id}): {str(e)}")
            return jsonify({
                "error": f"Stock is not found: {stock_symbol} (ID: {stock_id})",
                "suggestion": f"Please update the symbol for stock ID '{stock_id}' to a valid ticker."
            }), 404

        except Exception as e:
            logging.error(f"Error in stock_value: {str(e)}")
            return jsonify({"server error": str(e)}), 500

    def portfolio_value(self):
        """
        GET: Returns the total value of the portfolio along with the current date."""
        try:
            total_value = self.stock_service.get_portfolio_value()
            current_date = datetime.now().strftime("%d-%m-%Y")

            response = {
                "date": current_date,
                "portfolio value": total_value
            }
            return jsonify(response), 200

        except ValueError as e:
            # Log the invalid stock symbol error, but return a server error
            logging.error(f"Invalid stock symbol in portfolio: {str(e)}")
            return jsonify({
                "error": "Invalid stock symbol encountered in portfolio.",
                "suggestion": str(e)
            }), 500

        except Exception as e:
            logging.error(f"Error calculating portfolio value: {str(e)}")
            return jsonify({"server error": str(e)}), 500

    @staticmethod
    def kill_container():
        os._exit(1)

    @staticmethod
    def acquire_lock_with_retries(locks, resource, max_retries=4, retry_delay=2):
        """
        Tries to acquire a lock for the specified resource with retries.
        """
        for attempt in range(max_retries):
            lock_acquired = locks.acquire_lock(resource)
            if lock_acquired:
                logging.info(f"Lock acquired for resource '{resource}' on attempt {attempt + 1}.")
                return True
            else:
                logging.warning(
                    f"Lock attempt {attempt + 1} failed for resource '{resource}'. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)

        logging.warning(f"Failed to acquire lock for resource '{resource}' after {max_retries} attempts.")
        return False

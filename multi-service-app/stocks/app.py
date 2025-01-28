import os

from controller import StockController
from pymongo import MongoClient


def main():
    """
    Entry point for the Stock Portfolio Manager application.
    Initializes the StockController and runs the Flask app.
    """
    try:
        client = MongoClient("mongodb://mongodb-service:27017/")
        db = client["stock_portfolio_db"]
        stocks_collection = db["stock_portfolio_collection"]

        locks_delete_update_collection = db["locks_delete_update_collection"]
        locks_add_collection = db["locks_add_collection"]

        # Ensure the locks collection has the correct unique index on the "resource" field
        locks_delete_update_collection.create_index("resource", unique=True)
        locks_add_collection.create_index("resource", unique=True)

        controller = StockController(stocks_collection, locks_delete_update_collection, locks_add_collection)

        # Run the Flask app
        port = 8000
        controller.app.run(host='0.0.0.0', port=port)

    except Exception as e:
        print(f"Error starting the Stock Portfolio Manager: {str(e)}")


if __name__ == '__main__':
    main()
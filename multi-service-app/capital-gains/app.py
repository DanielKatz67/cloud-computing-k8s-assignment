import logging
import os

from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG to see detailed logs
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Read stock service ports from environment variables
STOCK_SERVICE_1_PORT = os.getenv("STOCK_SERVICE_1_PORT", "8000")
STOCK_SERVICE_2_PORT = os.getenv("STOCK_SERVICE_2_PORT", "8000")
STOCK_SERVICE_1_CONTAINER_NAME = os.getenv("STOCK_SERVICE_1_CONTAINER_NAME")
STOCK_SERVICE_2_CONTAINER_NAME = os.getenv("STOCK_SERVICE_2_CONTAINER_NAME")

# Dynamically construct URLs based on ports
STOCK_SERVICE_1_URL = f"http://{STOCK_SERVICE_1_CONTAINER_NAME}:{STOCK_SERVICE_1_PORT}/stocks"
STOCK_SERVICE_2_URL = f"http://{STOCK_SERVICE_2_CONTAINER_NAME}:{STOCK_SERVICE_2_PORT}/stocks"
STOCK_SERVICE_1_VALUE_URL = f"http://{STOCK_SERVICE_1_CONTAINER_NAME}:{STOCK_SERVICE_1_PORT}/stock-value"
STOCK_SERVICE_2_VALUE_URL = f"http://{STOCK_SERVICE_2_CONTAINER_NAME}:{STOCK_SERVICE_2_PORT}/stock-value"


def _fetch_stock_data(portfolio):
    """Fetch stock data from the appropriate service."""
    stock_data_1 = []
    stock_data_2 = []
    try:
        if not portfolio or portfolio == "stocks1":
            logging.info(f"Fetching data from {STOCK_SERVICE_1_URL}")
            stock_data_1 += requests.get(STOCK_SERVICE_1_URL).json()
        if not portfolio or portfolio == "stocks2":
            logging.info(f"Fetching data from {STOCK_SERVICE_2_URL}")
            stock_data_2 += requests.get(STOCK_SERVICE_2_URL).json()
    except requests.RequestException as e:
        logging.error(f"Error fetching data from stock services: {e}")
        raise
    return stock_data_1, stock_data_2


def _filter_stocks(stock_data, numSharesGt, numSharesLt):
    """Filter stocks based on query parameters."""
    return [
        stock for stock in stock_data
        if 'id' in stock and 'shares' in stock and 'purchase price' in stock and
           (numSharesGt is None or stock['shares'] > numSharesGt) and
           (numSharesLt is None or stock['shares'] < numSharesLt)
    ]


def _fetch_current_value(stock):
    """Fetch the current price for a specific stock based on its portfolio."""
    stock_value_url = (
        f"{STOCK_SERVICE_1_VALUE_URL}/{stock['id']}"
        if stock.get('portfolio') == "stocks1"
        else f"{STOCK_SERVICE_2_VALUE_URL}/{stock['id']}"
    )
    try:
        logging.info(f"Fetching current value for stock ID {stock['id']} from {stock_value_url}")
        response = requests.get(stock_value_url).json()
        return response.get("stock_value", 0)
    except requests.RequestException as e:
        logging.error(f"Error fetching current value for stock ID {stock['id']}: {e}")
        return 0


def _calculate_capital_gains(filtered_stocks):
    """Calculate total capital gains for filtered stocks."""
    capital_gains = 0
    for stock in filtered_stocks:
        current_value = _fetch_current_value(stock)
        stock_capital_gain = current_value - (stock['purchase price'] * stock['shares'])
        logging.info(
            f"Capital gain for stock {stock['symbol']}: "
            f"{current_value} - ({stock['purchase price']} * {stock['shares']}) = {stock_capital_gain}. "
            f"Current_value - (purchase price * shares)"
        )
        capital_gains += stock_capital_gain
    return capital_gains


@app.route('/capital-gains', methods=['GET'])
def get_capital_gains():
    logging.info("Received a request for capital gains")

    # Query parameters
    portfolio = request.args.get('portfolio')
    numSharesGt = request.args.get('numsharesgt', type=int)
    numSharesLt = request.args.get('numshareslt', type=int)
    logging.info(f"Query parameters - portfolio: {portfolio}, numSharesGt: {numSharesGt}, numSharesLt: {numSharesLt}")

    try:
        # Fetch and process stock data
        stock_data_1, stock_data_2 = _fetch_stock_data(portfolio)
        logging.info(f"Fetched stock data from portfolio 1: {stock_data_1}.")
        logging.info(f"Fetched stock data from portfolio 2: {stock_data_2}.")

        # Add portfolio information
        for stock in stock_data_1: stock['portfolio'] = "stocks1"
        for stock in stock_data_2: stock['portfolio'] = "stocks2"

        # Combine stock data into one list
        stock_data = stock_data_1 + stock_data_2

        filtered_stocks = _filter_stocks(stock_data, numSharesGt, numSharesLt)
        logging.info(f"Filtered stock data: {filtered_stocks}")

        capital_gains = round(_calculate_capital_gains(filtered_stocks), 2)
        logging.info(f"Calculated total capital gains: {capital_gains}")

        return jsonify({"capital-gains": capital_gains})
    except Exception as e:
        logging.error(f"Error processing capital gains request: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    port = int(os.getenv("FLASK_PORT", 8080))
    logging.info(f"Starting Capital Gain Service on port {port}")
    app.run(host='0.0.0.0', port=port)

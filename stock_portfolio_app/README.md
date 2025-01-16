# Stock Portfolio Management REST Application

This project is a REST application for managing a stock portfolio. It allows users to manage stocks in a given portfolio, retrieve stock prices, and compute the value of the portfolio based on the latest recorded prices. The application uses a 3rd party API to retrieve stock prices and runs in a Docker container.

## Architecture

The application follows a controller-service architecture, where the controller module handles incoming HTTP requests and invokes the appropriate methods in the service module. The service module contains the business logic for managing stocks, retrieving stock prices, and computing the portfolio value. It also interacts with a 3rd party API to retrieve stock prices.

## Features

- Manage stocks in a portfolio
- Retrieve stock prices on a given day
- Compute the value of the portfolio based on the latest recorded prices
- Use a 3rd party API to retrieve stock prices
- Run the application in a Docker container

## Endpoints

### POST /stocks
Add a new stock to the portfolio.
- **Request Body**: JSON object containing `symbol`, `purchase_price`, `shares`, and optionally `name` and `purchase_date`.
- **Responses**:
  - `201 Created`: Returns the JSON object with the `id` of the created stock.
  - `400 Bad Request`: Returns `{"error": "Malformed data"}` if the request body is invalid.
  - `415 Unsupported Media Type`: Returns `{"error": "Expected application/json media type"}` if the request content type is not JSON.
  - `500 Internal Server Error`: Returns `{"server error": "error message"}` if an unexpected error occurs.

### GET /stocks
Retrieve all stocks in the portfolio.
- **Responses**:
  - `200 OK`: Returns a JSON array of stock objects.
  - `500 Internal Server Error`: Returns `{"server error": "error message"}` if an unexpected error occurs.

### GET /stocks/\<stock_id\>
Retrieve a specific stock by its ID.
- **Responses**:
  - `200 OK`: Returns the JSON object of the stock.
  - `404 Not Found`: Returns `{"error": "Not found"}` if the stock is not found.
  - `500 Internal Server Error`: Returns `{"server error": "error message"}` if an unexpected error occurs.

### DELETE /stock/\<symbol\>
Remove a stock from the portfolio by its symbol.
- **Responses**:
  - `200 OK`: Returns a success message.
  - `404 Not Found`: Returns `{"error": "Not found"}` if the stock is not found.
  - `500 Internal Server Error`: Returns `{"server error": "error message"}` if an unexpected error occurs.

### GET /stock-value/\<symbol\>
Retrieve the current value of a stock in the portfolio.
- **Responses**:
  - `200 OK`: Returns the JSON object with the current value of the stock.
  - `400 Bad Request`: Returns `{"error": "Malformed data"}` if the symbol is invalid.
  - `500 Internal Server Error`: Returns `{"server error": "error message"}` if an unexpected error occurs.

### GET /portfolio-value
Retrieve the total value of the portfolio.
- **Responses**:
  - `200 OK`: Returns the JSON object with the total value of the portfolio.
  - `500 Internal Server Error`: Returns `{"server error": "error message"}` if an unexpected error occurs.

## Environment Variables

- `NINJA_API_KEY`: The API key for accessing the 3rd party stock price API.

## Setup

1. Clone the repository.
2. Create a `.env` file in the root of the project and add your NINJA API key:
    ```plaintext
    NINJA_API_KEY=your_secret_ninja_api_key
    ```
3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```
4. Run the application:
    ```sh
    python app.py
    ```

## Running in Docker

1. Build the Docker image:
    ```sh
    docker build -t stock-portfolio-app .
    ```
2. Run the Docker container:
    ```sh
    docker run -d -p 5000:5000 --env-file .env stock-portfolio-app
    ```

## Testing

To run the tests, use the following command:
```sh
pytest
# Tax Refund API

This service calculates estimated tax refunds based on property data.

## Requirements

* Python 3.10
* Docker

## Setup

1.  Clone the repository.
2.  (Optional) Create a virtual environment:

    ```bash
    python3.10 -m venv venv
    source venv/bin/activate   # On Linux/macOS
    # venv\Scripts\activate   # On Windows
    ```

3.  Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

* **Locally (for development):**

    ```bash
    python app.py
    ```

    The API will be available at `http://localhost:5000/refund`.

## Docker

* **Build the Docker image:**

    ```bash
    docker build -t tax-refund-api .
    ```

* **Run the Docker container:**

    ```bash
    docker run -p 5000:5000 tax-refund-api
    ```

    The API will be available at `http://localhost:5000/refund`.

* **Run the Test File:**

    ```bash
    docker run --rm tax-refund-api python test_app.py
    ```

## Testing

* Run the tests:

    ```bash
    python test_app.py
    ```

## API Endpoint

* `/refund` (POST)
    * Accepts a JSON payload: `{"pin": "26062070090000"}`
    * Returns a JSON response with the calculated refund data.

    ```json
    {
        "pin": "26062070090000",
        "yearsEligible": 4,
        "totalRefund": 7043.40
    }
    ```

## Configuration

* No environment variables are required. The application uses the provided `interest_rates.csv` file.

## Project Files

* `app.py`:  Flask application code.
* `interest_rates.csv`: CSV file containing yearly interest rates. 
* `pins.csv`: CSV file containing property PINs.
* `requirements.txt`: Python dependencies.
* `test_app.py`: Automated tests.
* `Dockerfile`: Docker configuration file.

## Refund Calculation Logic

The API calculates the estimated tax refund using the following logic:

1.  **Compare Values:**
    * Compute the average assessed value among comparable properties. 
    * If the property's assessed value is less than or equal to the average, the eligibility is zero. 
2.  **Determine Full-Year Occupancy:**
    * Extract the property's sale date from the comparables data. 
    * Count only full calendar years between the sale date and today (up to a maximum of 4 years). 
3.  **Yearly Refund Amount:**
    * For each full year, calculate the refund as: `refund = (property_value - average_comparable_value)`. 
4.  **Present Value Calculation:**
    * Adjust each year's refund to its present value using the interest rates. 
    * The formula used is:

        ```
        PVyeari = PMT * ((1 + r1) * (1 + r2) * ... * (1 + rn))
        ```

        Where:

        * `PVyeari` = the present value of the refund from year i
        * `PMT` = the calculated base amount for refund
        * `r1, r2, ..., rn` = the interest rates from the years between the start year and now
5.  **Total:**
    * Sum all the present-valued refunds.
    * If there are no eligible years, no comparables, or the property value is less than or equal to the average comparable value, the total refund is 0. 

## Additional Notes

* The comparables data is retrieved from an external API endpoint: `http://34.28.139.127:8082/comp?pin={{pin}}` 
* The PIN in the request payload should be stripped of any non-numeric characters. 
* Go to `https://www.cookcountyassessor.com/pin/{{pin}}` to learn more about an individual property. 

## Suggested Improvements:

### Verbose Parameter in API Response:

* Add a query parameter `?verbose=true` to the `/refund` endpoint to return a detailed breakdown of the refund calculation by year.
* This will provide more transparency into how the `totalRefund` is derived.
* Example of the extended response:

    ```json
    {
        "pin": "26062070090000",
        "yearsEligible": 3,
        "totalRefund": 7043.40,
        "breakdown": {
            "2021": 2100.50,
            "2022": 2450.30,
            "2023": 2492.60
        }
    }
    ```

### Enhanced Comparables Filtering:

* Currently, the API uses all comparable properties returned by the external API.
* To improve accuracy, consider filtering these comparables based on:
    * **Neighborhood Similarity:** Only include properties in the same or very similar neighborhoods. This assumes the comparables API provides neighborhood information.
    * **Market Similarity:** Further refine the selection by considering properties with similar characteristics (e.g., property type, age, style).
* **Weighted Comparables:**
    * Instead of a simple average, assign weights to each comparable property to give more importance to the most relevant ones.
    * Example: Weight by square footage similarity: `weight = 1 / abs(property_square_footage - comparable_square_footage)`.  Properties with closer square footage would have higher weights.
    * Other weighting factors could include:
        * Proximity
        * Age of property
        * Number of bedrooms/bathrooms

These enhancements would make the refund estimates more precise and provide users with more detailed information.
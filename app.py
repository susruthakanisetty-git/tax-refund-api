import re
from flask import Flask, request, jsonify
import csv
import requests
from datetime import datetime

app = Flask(__name__)

# Load interest rates
interest_rates = {}
with open('interest_rates.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['Year'] and row['Rate']:
            interest_rates[int(row['Year'])] = float(row['Rate'])

def calculate_full_calendar_years(sale_date, today):
    """
    Calculates the number of full calendar years between two dates.

    Args:
        sale_date (datetime): The sale date of the property.
        today (datetime): The current date.

    Returns:
        int: The number of full calendar years (up to a maximum of 4).
    """
    start_year = sale_date.year
    end_year = today.year
    years_eligible = 0

    # 1. Count all the years between start year and end year (excluding both)
    years_eligible = end_year - start_year - 1
    if years_eligible < 0: #Handle edge case where end_year <= start_year
        years_eligible = 0

    # 2. Include start year if start date is Jan 1
    if sale_date.month == 1 and sale_date.day == 1:
        years_eligible += 1

    # 3. Include end year if end date is Dec 31
    if today.month == 12 and today.day == 31:
        years_eligible += 1

    return min(years_eligible, 4)

def calculate_refund(pin, comparables_data):
    """
    Calculates the total refund for a given PIN.

    Args:
        pin (str): The Property Identification Number.
        comparables_data (dict): Data about the property and comparable properties.

    Returns:
        dict: A dictionary containing the pin, eligible years, and total refund.
    """ 
    
    property_data = comparables_data.get(pin)
    
    if not property_data:
        return {"pin": pin, "yearsEligible": 0, "totalRefund": 0}  
    
    pin_property = pin
    
    comparables = [data for pin, data in comparables_data.items() if pin != pin_property]

    if not comparables:
        return {"pin": pin, "yearsEligible": 0, "totalRefund": 0}

    total_weight = 0
    weighted_sum = 0
    property_square_foot= property_data.get('building sqft')
    if property_square_foot is None:
        avg_assessed_value = sum(comp['assessed value'] for comp in comparables) / len(comparables)
    else:
        #Calculate average based on square foot of comparables
        for comp in comparables:
            comparable_square_foot = comp.get('building sqft')
            if comparable_square_foot is not None:
                # Calculate weight based on square foot difference
                weight = 1 / (abs(property_square_foot - comparable_square_foot) + 1)  # Adding 1 to avoid division by zero
                total_weight += weight
                weighted_sum += comp['assessed value'] * weight
        avg_assessed_value = weighted_sum / total_weight if total_weight > 0 else 0
    
    if property_data['assessed value'] <= avg_assessed_value:
        return {"pin": pin, "yearsEligible": 0, "totalRefund": 0}
    
    sale_date_str = property_data.get('sale date')
    if not sale_date_str:
        return {"pin": pin, "yearsEligible": 0, "totalRefund": 0}  # Or handle missing sale date

    sale_date = datetime.strptime(sale_date_str, '%m/%d/%Y')  
    today = datetime.now()
    
    years_eligible = calculate_full_calendar_years(sale_date, today)
    total_refund = 0
    refund_amount = property_data['assessed value'] - avg_assessed_value
    for year_offset in range(1, years_eligible + 1):
        year = today.year - year_offset
        present_value = calculate_present_value(refund_amount, year, interest_rates, today.year)
        total_refund += present_value

    return {"pin": pin, "yearsEligible": years_eligible, "totalRefund": round(total_refund, 2)}


def calculate_present_value(amount, year, interest_rates, max_range):
    """
    Calculates the present value of a refund amount.

    Args:
        amount (float): The refund amount.
        year (int): The year for which to calculate the present value.
        interest_rates (dict): A dictionary of interest rates, where keys are years and values are rates.
        max_range (int): The current year (used as the upper bound for the calculation).

    Returns:
        float: The present value of the refund amount.
    """
    n = 1  
    geometric_product = 1
    for i in range(year, max_range):  
        rate = interest_rates.get(i)
        if rate is not None:
            geometric_product *= (1 + rate)
            n += 1
        else:
            return 0  

    return amount * geometric_product

@app.route('/refund', methods=['POST'])
def get_refund():
    """
    Endpoint to calculate the estimated tax refund for a given PIN.

    Returns:
        json: A JSON response containing the refund information.
    """
    data = request.get_json()
    if not data or 'pin' not in data:
        return jsonify({"error": "PIN is required"}), 400 # Return an error if PIN is missing
    pin = re.sub(r'[^0-9]', '', data['pin'])  # Removes ALL non-digits

    try:
        comparables_url = f'http://34.28.139.127:8082/comp?pin={pin}'
        comparables_response = requests.get(comparables_url)
        comparables_response.raise_for_status()  # Raise HTTPError for bad responses
        comparables_data = comparables_response.json()
        pin = list(comparables_data.keys())[0]
        refund_data = calculate_refund(pin, comparables_data)
        return jsonify(refund_data)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Error fetching comparables data: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
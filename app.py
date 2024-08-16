from flask import Flask, request, jsonify
import json
import re
import sqlite3
from difflib import SequenceMatcher
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Load data from various JSON files
with open('loans.json', 'r', encoding='utf-8') as file:
    ksfe_loans_data = json.load(file)

with open('int_rate.json', 'r', encoding='utf-8') as file:
    ksfe_interest_rates_data = json.load(file)

with open('deposite.json', 'r', encoding='utf-8') as file:
    deposit_data = json.load(file)

with open('que.json', 'r') as file:
    query_data = json.load(file)



app = Flask(__name__)

# Function to retrieve and display deposit schemes
def get_deposit_schemes():
    cursor.execute("SELECT scheme_name FROM DepositSchemes")
    schemes = cursor.fetchall()
    if schemes:
        return [scheme[0] for scheme in schemes]
    return []

# Function to retrieve and display loan schemes
def get_loan_schemes():
    cursor.execute("SELECT scheme_name FROM LoanSchemes")
    schemes = cursor.fetchall()
    if schemes:
        return [scheme[0] for scheme in schemes]
    return []

# Function to retrieve loan information based on user query
def get_loan_info(loan_type):
    for loan in ksfe_loans_data['Loans']:
        if loan['loan_type'].lower() == loan_type.lower():
            return loan
    return None

# Function to retrieve interest rates based on user query
def get_interest_rates(loan_type):
    for rates_info in ksfe_interest_rates_data['interest_rates']:
        if rates_info['scheme'].strip().lower() == loan_type.lower():
            return rates_info['rates']
    return None

# Function to handle deposit queries
def ksfe_deposit_chatbot(question):
    question = question.lower()  # Convert question to lowercase for case insensitivity
    if 'summary' in question or 'summary of deposit schemes' in question:
        return deposit_data['questions'][1]['answer']
    elif 'deposits' in question or 'deposit schemes' in question:
        return deposit_data['questions'][0]['answer']
    elif 'nettam plus' in question:
        return format_deposit_scheme(deposit_data['deposit_schemes']['nettam_plus'])
    elif 'vandanam' in question:
        return format_deposit_scheme(deposit_data['deposit_schemes']['vandanam'])
    elif 'fixed deposit' in question:
        return format_deposit_scheme(deposit_data['deposit_schemes']['fixed_deposit'])
    elif 'chitty security' in question:
        return format_deposit_scheme(deposit_data['deposit_schemes']['chitty_security_deposit'])
    elif 'short term deposit' in question:
        return format_deposit_scheme(deposit_data['deposit_schemes']['short_term_deposit'])
    elif 'sugama deposit' in question:
        return format_deposit_scheme(deposit_data['deposit_schemes']['sugama_deposit'])
    elif 'nettam deposit' in question:
        return format_deposit_scheme(deposit_data['deposit_schemes']['nettam_deposit'])
    else:
        return "Sorry"

# Function to format deposit scheme details
def format_deposit_scheme(scheme_data):
    details = scheme_data.get('details', {})

    formatted_details = []
    if 'duration' in details:
        formatted_details.append(f"- Duration: {details['duration']}")
    if 'minimum_amount' in details:
        formatted_details.append(f"- Minimum Amount: {details['minimum_amount']}")
    if 'interest_rate' in details:
        formatted_details.append(f"- Interest Rate: {details['interest_rate']}")
    if 'eligibility' in details:
        formatted_details.append(f"- Eligibility: {details['eligibility']}")
    if 'public_deposit_rate' in details:
        formatted_details.append(f"- Public Deposit Rate: {details['public_deposit_rate']}")
    if 'chitty_prize_money_deposit_rate' in details:
        formatted_details.append(f"- Chitty Prize Money Deposit Rate: {details['chitty_prize_money_deposit_rate']}")
    if 'senior_citizen_rate' in details:
        formatted_details.append(f"- Senior Citizen Rate: {details['senior_citizen_rate']}")
    if 'minimum_amount_for_interest_withdrawal' in details:
        formatted_details.append(f"- Minimum Amount for Interest Withdrawal: {details['minimum_amount_for_interest_withdrawal']}")
    if 'minimum_period' in details:
        formatted_details.append(f"- Minimum Period: {details['minimum_period']}")
    if 'maximum_period' in details:
        formatted_details.append(f"- Maximum Period: {details['maximum_period']}")
    if 'deposit_multiples' in details:
        formatted_details.append(f"- Deposit Multiples: {details['deposit_multiples']}")
    if 'usage_as_security' in details:
        formatted_details.append(f"- Usage as Security: {details['usage_as_security']}")
    if 'renewal_provision' in details:
        formatted_details.append(f"- Renewal Provision: {details['renewal_provision']}")
    if 'premature_closure' in details:
        formatted_details.append(f"- Premature Closure: {details['premature_closure']}")
    if 'interest_rates' in details:
        formatted_details.append("Interest Rates:")
        for period, rate in details['interest_rates'].items():
            formatted_details.append(f"  - {period.replace('_', ' ').capitalize()}: {rate}")

    return f"**{scheme_data['title']}**\n\n{scheme_data['about']}\n\nDetails:\n" + "\n".join(formatted_details)

# Function to find the most similar response in query_data if the main chatbot fails
def get_response(query, threshold=0.45):
    best_match = None
    highest_ratio = 0

    for item in query_data['queries']:
        match_ratio = SequenceMatcher(None, query.lower(), item['query'].lower()).ratio()
        if match_ratio > highest_ratio:
            highest_ratio = match_ratio
            best_match = item

    if highest_ratio >= threshold:
        return best_match['response']
    return "I'm sorry, I don't have information on that. Please contact your nearest KSFE branch for assistance."

# Function to get latitude and longitude from place name
def get_lat_lon(place_name):
    geolocator = Nominatim(user_agent="ksfe_locator")
    location = geolocator.geocode(place_name)
    if location:
        return (location.latitude, location.longitude)
    else:
        return None

# Function to get pincode from latitude and longitude
def get_pincode_from_latlon(lat, lon):
    geolocator = Nominatim(user_agent="ksfe_locator")
    location = geolocator.reverse((lat, lon), exactly_one=True)
    if location:
        return location.raw['address'].get('postcode')
    else:
        return None

# Function to find the closest branch by pincode
def find_closest_branch_by_pincode(pincode):
    cursor.execute("SELECT * FROM ksfe_branches")
    branches = cursor.fetchall()

    closest_branch = None
    min_diff = float('inf')

    for branch in branches:
        branch_pincode = branch[-1]  # Assuming pincode is the last column in the table

        if branch_pincode:
            diff = abs(int(branch_pincode) - int(pincode))

            if diff < min_diff:
                min_diff = diff
                closest_branch = branch

    return closest_branch

# Function to validate and process pincode
def validate_and_process_pincode(pincode):
    try:
        pincode = int(pincode)
        if pincode <= 0:
            raise ValueError("Invalid pincode")
        return pincode
    except (ValueError, TypeError):
        return None

@app.route('/chatbot', methods=['POST'])
def chatbot():
    user_input = request.json.get('message', '').strip().lower()

    # if 'type' in user_input or 'types' in user_input:
    #     if 'deposit' in user_input:
    #         deposit_schemes = get_deposit_schemes()
    #         return jsonify({"response": deposit_schemes})

    #     elif 'loan' in user_input:
    #         loan_schemes = get_loan_schemes()
    #         return jsonify({"response": loan_schemes})
    #     else:
    #         return jsonify({"response": "Sorry, I can only help with deposit or loan schemes."})

    if 'interest rate' in user_input:
        loan_type = user_input.replace('interest rate', '').strip()
        if loan_type:
            interest_rates = get_interest_rates(loan_type)
            if interest_rates:
                return jsonify({"response": interest_rates})
            else:
                return jsonify({"response": "Sorry, no interest rates available for this type."})

    # if 'nearest branch' in user_input:
    #     place_name = user_input.replace('nearest branch', '').strip()
    #     if place_name:
    #         lat_lon = get_lat_lon(place_name)
    #         if lat_lon:
    #             pincode = get_pincode_from_latlon(*lat_lon)
    #             if pincode:
    #                 closest_branch = find_closest_branch_by_pincode(pincode)
    #                 if closest_branch:
    #                     return jsonify({"response": f"Nearest branch is {closest_branch}"})
    #     return jsonify({"response": "Sorry, I couldn't find the nearest branch."})

    # Handling other cases or default fallback
    response = get_response(user_input)
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

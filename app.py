from flask import Flask, request, jsonify
import dill

# Load the chatbot model
with open('chatbot_model.pkl', 'rb') as f:
    chatbot_model = dill.load(f)

# Extract objects from the loaded model
get_deposit_schemes = chatbot_model["get_deposit_schemes"]
get_loan_schemes = chatbot_model["get_loan_schemes"]
get_loan_info = chatbot_model["get_loan_info"]
get_interest_rates = chatbot_model["get_interest_rates"]
ksfe_deposit_chatbot = chatbot_model["ksfe_deposit_chatbot"]
format_deposit_scheme = chatbot_model["format_deposit_scheme"]
get_response = chatbot_model["get_response"]
get_lat_lon = chatbot_model["get_lat_lon"]
get_pincode_from_latlon = chatbot_model["get_pincode_from_latlon"]
find_closest_branch_by_pincode = chatbot_model["find_closest_branch_by_pincode"]
validate_and_process_pincode = chatbot_model["validate_and_process_pincode"]
chatbot_function = chatbot_model["chatbot"]

# Initialize Flask app
app = Flask(__name__)

@app.route('/chatbot', methods=['POST'])
def chatbot():
    user_input = request.json.get('message')
    
    # Use the chatbot function to generate a response
    response = chatbot_function(user_input)
    
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True)


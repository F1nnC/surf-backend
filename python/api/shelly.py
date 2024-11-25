import logging
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from data.surf_data_fetcher import spot_data_time
import time
import requests

shelly_bp = Blueprint('shelly_bp', __name__)

# Test the connection to the Ollama service
@shelly_bp.route('/test_connection', methods=['GET'])
def test_connection():
    try:
        response = requests.get("http://localhost:11434")
        return jsonify({"msg": "Successfully connected to Ollama service", "status_code": response.status_code})
    except Exception as e:
        logging.error("Error connecting to Ollama service: %s", str(e))
        return jsonify({"msg": "Error connecting to Ollama service", "error": str(e)}), 500

# Main endpoint to handle user questions
@shelly_bp.route('/ask', methods=['POST'])
@jwt_required()
def ask():
    data = request.get_json()

    if not data:
        return jsonify({"msg": "No JSON data received"}), 400

    question = data.get('question')
    chat_history = data.get('chat_history', "")
    spots = data.get('spots')
    time_period = data.get('time_period')

    # Validate input data
    if not isinstance(question, str):
        return jsonify({"msg": "Question must be a string"}), 422
    if not isinstance(chat_history, str):
        return jsonify({"msg": "Chat history must be a string"}), 422
    if not isinstance(spots, list) or not all(isinstance(spot, str) for spot in spots):
        return jsonify({"msg": "Spots must be a list of strings"}), 422
    if time_period not in ["morning", "noon", "afternoon"]:
        return jsonify({"msg": "Invalid time period"}), 422

    # Fetch surf conditions for the provided spots and time period
    surf_data = []
    for spot_id in spots:
        spot_data = spot_data_time(spot_id, time_period)
        surf_data.extend(spot_data)

    # Define the prompt template for Shelly AI
    template = """
        Answer the following question with like a surfer accent.
        
        General Information to know, you are a surf condition helper AI called ShellyAI.
        
        People can give you questions about surf conditions and you can answer them.
        
        Please don't make up any information; only answer based on the surf data provided.
        This data shows the time period of the day where the person wants to go.
        
        Respond with only a sentence or two: 
        - In the first sentence, recommend a spot in a funny surfer language style.
        - In the second, give the data for why you recommend that spot.
        
        Surf conditions of the day: {surf_data}
        Question: {question}
    """

    # Initialize the Ollama model with the correct endpoint
    model = OllamaLLM(model="llama3.2:1b")
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model

    # Attempt to get a response from Ollama with retries
    max_retries = 3
    for attempt in range(max_retries):
        try:
            answer = chain.invoke({
                "question": question,
                "history": chat_history,
                "surf_data": surf_data
            })
            return jsonify({'answer': answer})
        except Exception as e:
            logging.error("Error invoking chain: %s", str(e))
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                return jsonify({"msg": "Error communicating with Ollama service", "error": str(e)}), 500

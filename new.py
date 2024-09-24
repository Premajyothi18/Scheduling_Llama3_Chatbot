import os
import requests
from dotenv import load_dotenv
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from flask import Flask, request, jsonify, render_template
import re

# Load environment variables from .env file
load_dotenv()

# Get the API key and handle missing environment variables
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
ollama_api_url = os.getenv("OLLAMA_API_URL", "https://scheduling-chatbot.onrender.com")
if not langchain_api_key:
    raise ValueError("LANGCHAIN_API_KEY is not set in the environment variables.")

# Set environment variables for langsmith tracking
os.environ["LANGCHAIN_API_KEY"] = langchain_api_key
os.environ["LANGCHAIN_TRACING_V2"] = "true"

# Create Flask app
app = Flask(__name__)

# WSGI application callable
wsgi = app

def initialize_chatbot(schedule_content):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a professional assistant. When the user asks for a schedule, respond with clear, concise points. Ensure each day or task is on a new line."),
            ("user", "Question: {question}\n\nRelevant Content:\n{schedule_content}")
        ]
    )

    # Initialize OpenAI LLM with the correct API URL
    llm = Ollama(model="llama3", api_url=ollama_api_url)  # Ensure this matches how your Ollama is set up
    
    # Initialize output parser
    output_parser = StrOutputParser()
    
    # Create chain
    chain = prompt | llm | output_parser
    return chain
def clean_output(response):
    # Example cleanup: remove excessive newlines, redundant words, or unwanted characters
    response = response.replace('\n\n', '\n')  # Remove double newlines
    response = re.sub(r'\s{2,}', ' ', response)  # Replace multiple spaces with a single space
    response = response.replace('+', '')  # Remove all `+` symbols
    response = response.replace('*', '')  # Remove all '*' character
    return response

def process_response(response):
    # Clean the response first
    cleaned_response = clean_output(response)
    # Split the response into points based on newlines
    points = cleaned_response.split('\n')
    # Remove empty points and strip leading/trailing whitespace
    points = [point.strip() for point in points if point.strip()]
    return points

def load_preloaded_data():
    data = {}
    base_path = r'C:\Users\PREMA\Desktop\LLama_Chatbot_Project\preloaded_schedules'

    # Ensure the directory exists
    if not os.path.exists(base_path):
        os.makedirs(base_path)

    for filename in os.listdir(base_path):
        file_path = os.path.join(base_path, filename)
        if os.path.isfile(file_path) and filename.endswith(".txt"):
            data_name = filename.replace('.txt', '')
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data[data_name] = file.read()
            except Exception as e:
                print(f"Error reading file {filename}: {str(e)}")
    return data

# Example usage in a Flask route
@app.route('/generate', methods=['POST'])
def generate_response():
    prompt = request.json.get('prompt', '')
    
    # Use the ollama_api_url environment variable from Render
    payload = {
        "model": "llama3",  # Ensure the model name matches what your API expects
        "prompt": prompt
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        # Use the ollama_api_url environment variable
        response = requests.post(f"{ollama_api_url}/api/generate", json=payload, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        
        result = response.json()
        print(f"Ollama API Response: {result}")  # Log the API response for debugging
        return jsonify(result)  # Send the response back to the client
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {str(e)}")  # Log the error
        return {"error": "Failed to generate response", "details": str(e)}, 500  # Return error with details
    
# Define route for home page
@app.route('/', methods=['GET', 'POST'])
def home():
    input_text = ""
    output = []
    error_message = ""
    
    try:
        # Load preloaded schedules and other data
        preloaded_data = load_preloaded_data()
    except Exception as e:
        error_message = f"An error occurred while loading data: {str(e)}"
        preloaded_data = {}

    if request.method == 'POST':
        input_text = request.form.get('input_text', '').strip()
        
        if input_text:
            try:
                # Initialize chatbot with some schedule content
                schedule_content = "Your schedule content here"
                chain = initialize_chatbot(schedule_content)
                
                # Generate response from the chatbot
                response = chain.invoke({'question': input_text, 'schedule_content': schedule_content})
                output = process_response(response)
            except Exception as e:
                error_message = f"An error occurred while generating response: {str(e)}"

    return render_template('index.html', input_text=input_text, output=output, error_message=error_message)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
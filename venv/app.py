import os
from dotenv import load_dotenv
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from flask import Flask, request, render_template
import re

# Load environment variables from .env file
load_dotenv()

# Set environment variables for langsmith tracking
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"

# Create Flask app
app = Flask(__name__)

def load_file_content(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        print(f"Error loading file: {str(e)}")
        return ""

# Define chatbot initialization
def initialize_chatbot(file_content):
    # Create chatbot prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a professional assistant. When the user asks for a schedule, respond with clear, concise points. Ensure each day or task is on a new line."),
            ("user", "Question: {question}\n\nReference Content:\n{file_content}")
        ]
    )
    
    # Initialize OpenAI LLM and output parser
    llm = Ollama(model="llama3")
    output_parser = StrOutputParser()
    
    # Create chain
    chain = prompt | llm | output_parser
    return chain

# Initialize chatbot
chain = initialize_chatbot(load_file_content)

def clean_output(response):
    # Example cleanup: remove excessive newlines, redundant words, or unwanted characters
    response = response.replace('\n\n', '\n')  # Remove double newlines
    response = re.sub(r'\s{2,}', ' ', response)  # Replace multiple spaces with a single space
    response = response.replace('+', '')  # Remove all `+` symbols
    return response

def process_response(response):
    # Clean the response first
    cleaned_response = clean_output(response)
    # Split the response into points based on newlines
    points = cleaned_response.split('\n')
    # Remove empty points and strip leading/trailing whitespace
    points = [point.strip() for point in points if point.strip()]
    return points

# Define route for home page
@app.route('/', methods=['GET', 'POST'])
def home():
    input_text = ""
    output = []
    error_message = ""
    # Load the file content once when the app starts
    file_content = load_file_content('test-syllabus.txt')  # Replace with your file path
    # Initialize the chatbot with the loaded file content
    #chain = initialize_chatbot(file_content)
    if request.method == 'POST':
        input_text = request.form.get('input_text', '').strip()
        if input_text:
            try:
                # Check if the user is asking for a schedule-related query
                #if re.search(r'\bschedule\b|\bplan\b|\bweek\b', input_text, re.IGNORECASE):
                    # Use the chatbot to get a structured response
                    #response = chain.invoke({'question': input_text})
                    #output = process_response(response)
                    # Pass the input_text and file content to the chatbot
                response = chain.invoke({'question': input_text, 'file_content': file_content})
                output = process_response(response)
                #else:
                    # Handle other types of queries normally
                    #response = chain.invoke({'question': input_text})
                    #output = process_response(response)
            except Exception as e:
                error_message = f"An error occurred: {str(e)}"
    
    return render_template('index.html', input_text=input_text, output=output, error_message=error_message)

if __name__ == '__main__':
    app.run(debug=True)
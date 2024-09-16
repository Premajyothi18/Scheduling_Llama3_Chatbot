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

# WSGI application callable
wsgi = app

def load_file_content(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        print(f"Error loading file: {str(e)}")
        return ""
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
    
def load_uploaded_schedules(files):
    uploaded_data = {}
    for file in files:
        try:
            data_name = file.filename.replace('.txt', '')
            uploaded_data[data_name] = file.read().decode('utf-8')
        except Exception as e:
            print(f"Error reading uploaded file {file.filename}: {str(e)}")
    return uploaded_data

# Define chatbot initialization
def initialize_chatbot(schedule_content):
    # Get the Ollama API URL from environment variables or use default
    ollama_api_url = os.getenv("OLLAMA_API_URL", 'http://localhost:11434/api/chat')
    # Create chatbot prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a professional assistant. When the user asks for a schedule, respond with clear, concise points. Ensure each day or task is on a new line."),
            ("user", "Question: {question}\n\nRelevant Content:\n{schedule_content}")
        ]
    )
    
    # Initialize OpenAI LLM and output parser
    llm = Ollama(model="llama3")
    output_parser = StrOutputParser()
    
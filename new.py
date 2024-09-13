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
    
    # Create chain
    chain = prompt | llm | output_parser
    return chain

# Initialize chatbot
#chain = initialize_chatbot()

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

# Define route for home page
@app.route('/', methods=['GET', 'POST'])
def home():
    input_text = ""
    output = []
    error_message = ""
    
    # Load preloaded schedules and other data
    preloaded_data = load_preloaded_data()

    if request.method == 'POST':
        input_text = request.form.get('input_text', '').strip()
        
        # Handle multiple file uploads
        uploaded_files = request.files.getlist('files')
        uploaded_data = load_uploaded_schedules(uploaded_files)
        
        # Combine preloaded and uploaded schedules
        combined_data = {**preloaded_data, **uploaded_data}
        
        # Here, you can either:
        # 1. Use specific schedules based on user query (e.g., "week 1", "department A")
        # 2. Or combine all relevant data
        selected_data = []
        if "week 1" in input_text.lower():
            selected_data.append(combined_data.get('week_1_schedule', ''))
        if "general schedule" in input_text.lower():
            selected_data.append(combined_data.get('general_schedule', ''))
        # Add more logic as needed

        combined_content = "\n".join(selected_data)
        
        if input_text:
            try:
                # Initialize chatbot with the combined content
                chain = initialize_chatbot(combined_content)
                response = chain.invoke({'question': input_text, 'schedule_content': combined_content})
                output = process_response(response)
            except Exception as e:
                error_message = f"An error occurred: {str(e)}"
    
    return render_template('index.html', input_text=input_text, output=output, error_message=error_message)
if __name__ == '__main__':
    app.run(debug=True)
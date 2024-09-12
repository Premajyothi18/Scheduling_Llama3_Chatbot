import ollama

syllabus_file_path = './test-syllabus.txt'

def read_syllabus(file_path):
    with open(file_path, 'r') as file:
        syllabus_content = file.read()
    return syllabus_content

def generate_curriculum(syllabus, weeks):
    url = 'http://localhost:11434/api/chat'
    
    response = ollama.chat(model='llama3.1', messages=[
        {
            'role': 'user',
            'content': f"Create a curriculum to cover the following course syllabus in {weeks} weeks:\n{syllabus}",
        },
    ])
    
    return response['message']['content']

def main():
    syllabus = read_syllabus(syllabus_file_path)
    
    weeks = input("Enter the number of weeks to complete the course: ")
    #days = input("Enter the days to complete the syllabus:")
    
    curriculum = generate_curriculum(syllabus, weeks)
    
    print("\nGenerated Curriculum:")
    print(curriculum)

if __name__ == "__main__":
    main()
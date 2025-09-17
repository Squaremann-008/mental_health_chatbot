import re
import json
from ollama import chat
from ollama import ChatResponse
from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def load_extracts(file_path):
    """
    Loads the text file and extracts the content.
    
    Args:
        file_path (str): The path to the text file.
        
    Returns:
        str: The extracted content from the file.
    """
    with open(file_path, 'r') as file:
        content = file.read()
    
    return content



def clean_text(text):
    """
    Cleans the input text by removing unwanted characters and formatting.
    
    Args:
        text (str): The input text to be cleaned.
        
    Returns:
        str: The cleaned text.
    """
    # Remove page notations
    text = re.sub(r"=== Page \d+ \(\d+ cols\) ===", "", text)
    
    # Remove special characters and extra spaces
    text = re.sub(r"\n", " ", text)
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text




def chunk_text(text, chunk_size=1500):
    """
    Splits the text into smaller chunks of a specified size.
    
    Args:
        text (str): The input text to be chunked.
        chunk_size (int): The maximum size of each chunk.
        
    Returns:
        list: A list of text chunks.
    """
    # Split the text into words
    text_splitter = RecursiveCharacterTextSplitter(
        # Set a really small chunk size, just to show.
        chunk_size=chunk_size,
        chunk_overlap=50,
        length_function=len,
        is_separator_regex=False,
    )
    texts = text_splitter.create_documents([text])
    return texts




def generate_conversation(chunks: list, DATASET_GEN_PROMPT:str) -> list:
    generated_conversations = []
    for chunk in chunks:
        d= chunk.page_content
        prompt = DATASET_GEN_PROMPT.format(chunk_text=d)
        response: ChatResponse = chat(
        model='llama3.2',  
        messages=[
            {"role": "system", "content": prompt},  # System message to set the context
            {"role": "user", "content": "Please help me with this situation."}  
        ]
        )

        generated_conversations.append(response.message['content'])
    return generated_conversations




def extract_json_response(generated_conversations: list) -> list:
    """
    Extracts and parses a JSON object from a string containing JSON data.
    
    Args:
        generated_conversations (list): List of strings containing JSON data.
        
    Returns:
        list: List containing parsed JSON objects cleaned/converted from the strings.
        
    Raises:
        ValueError: If any string in the list doesn't contain valid JSON.
    """
    list_of_jsons = []
    for i, conversation in enumerate(generated_conversations, 1):
        try:
            # Remove any leading/trailing whitespace or newlines and extract JSON content
            start = conversation.find('{')
            end = conversation.rfind('}') + 1
            
            if start == -1 or end == -1:
                raise ValueError(f"Invalid JSON format in conversation with index: {i}.")
            
            json_str = conversation[start:end]
            data = json.loads(json_str)
            
            # Append the valid JSON data to the list
            list_of_jsons.append(data)
            
        except json.JSONDecodeError as e:
            # Log the error and continue with the next conversation
            print(f"Skipping invalid JSON at index {i}: {e}")
        except ValueError as e:
            # Log and skip invalid JSON format
            print(f"Skipping conversation {i}: {e}")
    
    return list_of_jsons
    


import os
import sys
import json
import logging
from therapist_creation.utils.data_gen_prompt import DATASET_GEN_PROMPT
from therapist_creation.utils.data_prep import load_extracts, clean_text, chunk_text, generate_conversation, extract_json_response

# logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '/Users/mac/Documents/mental_engine_chatbot/therapist_creation')))

def generate(extracts_path, output_path):
    for extracted_books in os.listdir(extracts_path):
        extracted_path = os.path.join(extracts_path, extracted_books)
        try:
            loaded_extract = load_extracts(extracted_path)
            cleaned_text = clean_text(loaded_extract)
            logger.info("Successfully cleaned text")
            
            chunks = chunk_text(cleaned_text)
            logger.info("Done chunking text")
            
            generated_conversations = generate_conversation(chunks, DATASET_GEN_PROMPT)
            logger.info("Successfully generated conversations")
            
            list_of_jsons = extract_json_response(generated_conversations)
            
            save_path = os.path.join(output_path, f"{extracted_books}_synthetic_data.json")
            with open(save_path, 'w') as f:
                for json_obj in list_of_jsons:
                    f.write(json.dumps(json_obj) + '\n')
            logger.info(f"Successfully generated synthetic data from {extracted_books}!")

        except Exception as e:
            logger.error(f"Error processing {extracted_books}: {e}")
    

if __name__ == "__main__":
    extracts_path = "/Users/mac/Documents/mental_engine_chatbot/therapist_creation/extracted_books"
    output_path = "/Users/mac/Documents/mental_engine_chatbot/therapist_creation/synthetic_data"

    generate(extracts_path, output_path)
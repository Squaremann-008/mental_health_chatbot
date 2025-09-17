import os
import json
from utils.data_gen_prompt import DATASET_GEN_PROMPT
from utils.data_prep import load_extracts, clean_text, chunk_text, generate_conversation, extract_json_response




extracts_path = "/Users/mac/Documents/mental_engine_chatbot/therapist_creation/extracted_books"
output_path = "/Users/mac/Documents/mental_engine_chatbot/therapist_creation/synthetic_data"
for extracted_books in os.listdir(extracts_path):
    extracted_path= os.path.join(extracts_path, extracted_books)
    loaded_extract= load_extracts(extracted_path)
    cleaned_text = clean_text(loaded_extract)
    chunks= chunk_text(cleaned_text)
    generated_conversations = generate_conversation(chunks, DATASET_GEN_PROMPT)
    list_of_jsons = extract_json_response(generated_conversations)
    save_path = os.path.join(output_path, f"{extracted_books}_synthetic_data.json")
    with open(save_path, 'w') as f:
        for json_obj in list_of_jsons:
            f.write(json.dumps(json_obj) + '\n')


    

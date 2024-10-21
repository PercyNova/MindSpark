#Import statements and initial setup
import json
import os
import pyttsx3
from fuzzywuzzy import fuzz

#Text-to-speech setup
engine = pyttsx3.init()

def init_tts():
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)  
    engine.setProperty('volume', 1)  
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)  
    return engine

def speak(text):
    print(text)
    engine.say(text)
    engine.runAndWait()

#File path setup
json_directory = '../datasets/



FAQ loading function
def preload_all_faqs():
    all_faqs = []
    
    # Load common FAQs
    common_faqs_path = os.path.join(json_directory, 'common_FAQs.json')
    if os.path.exists(common_faqs_path):
        with open(common_faqs_path, 'r') as file:
            common_faqs = json.load(file).get("FAQs", [])
            for faq in common_faqs:
                faq['question'] = faq['question'].lower()
                faq['answer'] = faq['answer'].lower()
            all_faqs.extend(common_faqs)
    
    # Load disease-specific FAQs
    for disease, keywords in {**STI_DICTIONARY, **DISEASE_DICTIONARY}.items():
        file_name = f"{disease.replace(' ', '_').replace('/', '_').lower()}_data.json"
        file_path = os.path.join(json_directory, file_name)
        if os.path.exists(file_path):
            with open(file_path, 'r') as json_file:
                disease_faqs = json.load(json_file).get("FAQs", [])
                for faq in disease_faqs:
                    if 'question' in faq and 'answer' in faq:
                        faq['question'] = faq['question'].lower()
                        faq['answer'] = faq['answer'].lower()
                all_faqs.extend(disease_faqs)
    
    return all_faqs

#Best match finding function
def find_best_match(user_question, faqs):
    best_match = None
    highest_score = 0
    user_question = user_question.lower()
    
    for faq in faqs:
        if 'question' not in faq or 'answer' not in faq:
            speak(f"Warning: Missing 'question' or 'answer' in FAQ entry: {faq}")
            print(f"Warning: Missing 'question' or 'answer' in FAQ entry: {faq}")
            continue
        
        question = faq['question']
        score = fuzz.token_set_ratio(user_question, question)
        if score > highest_score:
            highest_score = score
            best_match = faq

    return best_match, highest_score

#FAQ search function
def search_faq(user_input, faqs):
    matched_faq, score = find_best_match(user_input, faqs)
    if matched_faq and score > 75:
        return matched_faq
    return None

#Main question asking loop
def ask_question():
    all_faqs = preload_all_faqs()
    speak("FAQs have been preloaded. You can now ask any question.")
    print("FAQs have been preloaded. You can now ask any question.")

    while True:
        speak("Ask a question (or type 'exit' to quit)")
        user_input = input("Ask a question (or type 'exit' to quit): ").strip()
        
        if user_input.lower() == "exit":
            speak("Goodbye!")
            break
        else:
            matched_faq, score = find_best_match(user_input, all_faqs)
            if matched_faq and score > 75:
                speak(f"\nQ: {matched_faq['question']}")
                speak(f"A: {matched_faq['answer']}\n")
            else:
                speak("No similar FAQ found.")
                print("No similar FAQ found.")

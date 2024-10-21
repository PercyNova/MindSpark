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
json_directory = r'C:\Users\cweng\Documents\GitHub\MindSpark\MindSpark AI Project\Python\Datasets\JSON'


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

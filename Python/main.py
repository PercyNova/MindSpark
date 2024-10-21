# Software Developer: Import statements and initial setup
import os
import json
import random
import pyttsx3
from fuzzywuzzy import fuzz
from json_questions import search_faq, STI_DICTIONARY, DISEASE_DICTIONARY, preload_all_faqs
from symptom_processing import detect_symptoms_from_input, process_multiple_symptoms, ALL_SYMPTOMS

# Software Developer: Text-to-speech setup
def init_tts():
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)  
    engine.setProperty('volume', 1)  
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)  
    return engine

def speak_text(engine, text):
    engine.say(text)
    engine.runAndWait()

#Main HealthQueryProcessor class
class HealthQueryProcessor:
    def __init__(self):
        #File path setup
        self.json_directory = r'C:\Users\cweng\Documents\GitHub\MindSpark\MindSpark AI Project\Python\Datasets\JSON'
        self.severity_dict_path = os.path.join(self.json_directory, 'severity_dict.json')
        self.common_faqs_path = os.path.join(self.json_directory, 'common_FAQs.json')
        self.excel_path = r'C:\Users\cweng\Documents\GitHub\MindSpark\MindSpark AI Project\Python\Datasets\CSV\symptom_data.xlsx'
        self.load_data()
        self.tts_engine = init_tts()  
        self.issued_tickets = {}
        self.ticket_counter = 1

        #Appointment Type
        self.appointment_dict = {
            'Routine Checkup': 'RC',
            'Dental Appointment': 'DA',
            'Pediatric Appointment': 'PA',
            'Surgical Consultation': 'SC',
            'Emergency Visit': 'EV',
            'Radiology Appointment': 'RA',
            'Physical Therapy': 'PT'
        }



    #Disease detection method
    def detect_disease(self, text):
        processed_text = text.lower()
        for disease, keywords in self.disease_dict.items():
            for keyword in keywords:
                if keyword.lower() in processed_text:
                    return disease
        return None

    #Disease query handling method
    def handle_disease_query(self, disease, user_input):
        disease_faqs = [faq for faq in self.all_faqs if faq.get('disease') == disease]
        if disease_faqs:
            best_match = None
            highest_score = 0
            for faq in disease_faqs:
                score = fuzz.ratio(user_input.lower(), faq['question'].lower())
                if score > highest_score:
                    highest_score = score
                    best_match = faq
            if best_match and highest_score > 60:
                return {
                    'type': 'disease',
                    'question': best_match['question'],
                    'answer': best_match['answer']
                }
        return None

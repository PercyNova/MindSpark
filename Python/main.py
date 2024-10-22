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
        self.json_directory ='../datasets'
        self.severity_dict_path = os.path.join(self.json_directory, 'severity_dict.json')
        self.common_faqs_path = os.path.join(self.json_directory, 'common_FAQs.json')
        self.excel_path =../datasets/symptom_data.xlsx'
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

    #Symptom severity checking method
    def check_symptom_severity(self, symptoms):
        matched_symptoms, severity_level, diseases = process_multiple_symptoms(symptoms, self.excel_path)
        return severity_level

    #Symptom query handling method
    def handle_symptom_query(self, initial_symptoms):
        all_symptoms = initial_symptoms.copy()
        
        while True:
            user_input = input("Enter additional symptoms (if any), or press Enter to continue: ").strip()
            if not user_input:
                break
            additional_symptoms = detect_symptoms_from_input(user_input, ALL_SYMPTOMS)
            all_symptoms.extend(additional_symptoms)

        matched_symptoms, severity, top_diseases = process_multiple_symptoms(all_symptoms, self.excel_path)
        
        if matched_symptoms:
            return {
                'type': 'symptoms',
                'matched_symptoms': matched_symptoms,
                'severity': severity,
                'top_diseases': top_diseases
            }
        else:
            return {
                'type': 'unknown',
                'message': "No matching symptoms were found."
            }

    # Software Developer: Main query processing method
    def process_query(self, user_input):
        if "make an appointment" in user_input.lower():
            return self.generate_ticket()

        # Step 1: Detect symptoms
        symptoms = detect_symptoms_from_input(user_input, ALL_SYMPTOMS)
        if symptoms:
            return self.handle_symptom_query(symptoms)
        
        # Step 2: Detect diseases or search FAQ if no symptoms
        disease = self.detect_disease(user_input)
        if disease:
            result = self.handle_disease_query(disease, user_input)
            if result:
                return result

        # Step 3: Search FAQs if no disease detected
        faq_result = search_faq(user_input, self.all_faqs)
        if faq_result:
            return {
                'type': 'faq',
                'question': faq_result['question'],
                'answer': faq_result['answer']
            }
        
        return {'type': 'unknown', 'message': "Sorry, I couldn't understand your query."}

    #Appointment ticket generation method
    def generate_ticket(self):
        # Step 1: Get user initials
        initials = input("Enter your initials: ").upper()
        
        # Step 2: Select appointment type from the dictionary
        print("Select an appointment type:")
        for i, appointment in enumerate(self.appointment_dict.keys(), start=1):
            print(f"{i}. {appointment}")
        
        choice = int(input("Enter the number of your choice: "))
        appointment_type = list(self.appointment_dict.keys())[choice - 1]

        # Step 3: Check symptom severity
        severity = self.check_symptom_severity([]) 
        severity_code = {'Mild': '1', 'Moderate': '2', 'Severe': '3'}.get(severity, 'Unknown')

        # Step 4: Generate the ticket number
        current_ticket_number = f'{self.ticket_counter:03}'  
        ticket_code_parts = [severity_code, self.appointment_dict[appointment_type], initials, current_ticket_number]
        random.shuffle(ticket_code_parts)  
        generated_ticket = ''.join(ticket_code_parts)  

        # Step 5: Ensure unique ticket generation (avoid duplicates)
        while generated_ticket in self.issued_tickets:
            self.ticket_counter += 1  
            current_ticket_number = f'{self.ticket_counter:03}'
            ticket_code_parts[-1] = current_ticket_number  
            random.shuffle(ticket_code_parts) 
            generated_ticket = ''.join(ticket_code_parts)

        # Step 6: Store ticket details in issued_tickets dictionary
        self.issued_tickets[generated_ticket] = {
            'initials': initials,
            'appointment_type': appointment_type,
            'severity': severity
        }
        self.ticket_counter += 1  # Increment ticket counter after issuing

        # Step 7: Output and return the generated ticket
        speak_text(self.tts_engine, f"Your appointment ticket is {generated_ticket}.")
        print(f"Your ticket is: {generated_ticket}")
        print(f"Full Ticket Information: Severity: {severity}, Appointment Type: {appointment_type}, Ticket Number: {current_ticket_number}")
        
        return generated_ticket

#Main function
def main():
    processor = HealthQueryProcessor()
    
    print("Welcome to the Health Query System!")
    
    print("Describe your symptoms, ask about diseases, or ask general health questions.")
    print("Type 'quit' to exit.")

    while True:
        user_input = input("\nPlease enter your question or describe your symptoms: ").strip()
        if user_input.lower() == 'quit':
            print("Thank you for using the Health Query System. Goodbye!")
            break
            
        result = processor.process_query(user_input)

        if result['type'] == 'disease':
            speak_text(processor.tts_engine, f"Q: {result['question']} A: {result['answer']}")
            print(f"\nQ: {result['question']}")
            print(f"A: {result['answer']}")
        elif result['type'] == 'symptoms':
            speak_text(processor.tts_engine, f"Matched symptoms are: {', '.join(result['matched_symptoms'])} Severity: {result['severity']}")
            print("\nSymptom Analysis:")
            print(f"Matched Symptoms: {', '.join(result['matched_symptoms'])}")
            print(f"Severity Level: {result['severity']}")
            if result['top_diseases']:
                print("Top matched diseases based on symptoms:")
                for disease in result['top_diseases']:
                    print(f"- {disease[0]} (Severity: {disease[4]})")
        elif result['type'] == 'faq':
            speak_text(processor.tts_engine, f"Q: {result['question']} A: {result['answer']}")
            print(f"\nQ: {result['question']}")
            print(f"A: {result['answer']}")
        else:
            speak_text(processor.tts_engine, result['message'])
            print(result['message'])

if __name__ == "__main__":
    main()

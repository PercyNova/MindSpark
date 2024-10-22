from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import json
import os
import random
from fuzzywuzzy import fuzz

# Import functionality from your existing system
from symptom_processing import (
    detect_symptoms_from_input,
    process_multiple_symptoms,
    ALL_SYMPTOMS
)
from json_questions import (
    search_faq,
    STI_DICTIONARY,
    DISEASE_DICTIONARY,
    preload_all_faqs
)

class HealthQuerySystem:
    def __init__(self):
        self.json_directory = '../datasets/'
        self.excel_path = r'../datasets/symptom_data.xlsx'
        self.issued_tickets = {}
        self.ticket_counter = 1
        self.all_faqs = preload_all_faqs()
        self.disease_dict = {**STI_DICTIONARY, **DISEASE_DICTIONARY}
        self.appointment_dict = {
            'Routine Checkup': 'RC',
            'Dental Appointment': 'DA',
            'Pediatric Appointment': 'PA',
            'Surgical Consultation': 'SC',
            'Emergency Visit': 'EV',
            'Radiology Appointment': 'RA',
            'Physical Therapy': 'PT'
        }

class ActionCheckSymptoms(Action):
    def name(self) -> Text:
        return "action_check_symptoms"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get('text', '')
        symptoms = detect_symptoms_from_input(user_message, ALL_SYMPTOMS)
        
        if not symptoms:
            dispatcher.utter_message(text="I couldn't detect any specific symptoms in your message. Could you please describe your symptoms more clearly?")
            return []

        matched_symptoms, severity, top_diseases = process_multiple_symptoms(symptoms, HealthQuerySystem().excel_path)
        
        response = f"I've detected the following symptoms: {', '.join(matched_symptoms)}\n"
        response += f"Severity Level: {severity}\n"
        
        if top_diseases:
            response += "\nPossible related conditions:\n"
            for disease in top_diseases[:3]:
                response += f"- {disease[0]} (Severity: {disease[4]})\n"
        
        dispatcher.utter_message(text=response)
        
        return [SlotSet("severity_level", severity),
                SlotSet("detected_symptoms", matched_symptoms)]

class ActionSearchFAQ(Action):
    def name(self) -> Text:
        return "action_search_faq"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get('text', '')
        health_system = HealthQuerySystem()
        
        # First try to find disease-specific information
        for disease, keywords in health_system.disease_dict.items():
            if any(keyword.lower() in user_message.lower() for keyword in keywords):
                disease_faqs = [faq for faq in health_system.all_faqs if faq.get('disease') == disease]
                if disease_faqs:
                    best_match = max(disease_faqs, 
                                   key=lambda x: fuzz.ratio(user_message.lower(), x['question'].lower()))
                    if fuzz.ratio(user_message.lower(), best_match['question'].lower()) > 60:
                        dispatcher.utter_message(text=f"Q: {best_match['question']}\nA: {best_match['answer']}")
                        return []

        # If no disease-specific match, search general FAQs
        faq_result = search_faq(user_message, health_system.all_faqs)
        if faq_result:
            dispatcher.utter_message(text=f"Q: {faq_result['question']}\nA: {faq_result['answer']}")
        else:
            dispatcher.utter_message(text="I couldn't find a specific answer to your question. Could you please rephrase it?")
        
        return []

class ActionScheduleAppointment(Action):
    def name(self) -> Text:
        return "action_schedule_appointment"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        health_system = HealthQuerySystem()
        
        # Get user initials from slot
        initials = tracker.get_slot("user_initials")
        if not initials:
            dispatcher.utter_message(text="Please provide your initials to schedule an appointment.")
            return []
        
        # Get appointment type from slot
        appointment_type = tracker.get_slot("appointment_type")
        if not appointment_type or appointment_type not in health_system.appointment_dict:
            dispatcher.utter_message(text="Please select a valid appointment type:\n" + 
                                  "\n".join([f"- {apt_type}" for apt_type in health_system.appointment_dict.keys()]))
            return []
        
        # Get severity level from previous symptom check or default to Mild
        severity = tracker.get_slot("severity_level") or "Mild"
        severity_code = {'Mild': '1', 'Moderate': '2', 'Severe': '3'}.get(severity, '1')
        
        # Generate ticket
        current_ticket_number = f'{health_system.ticket_counter:03}'
        ticket_code_parts = [
            severity_code,
            health_system.appointment_dict[appointment_type],
            initials.upper(),
            current_ticket_number
        ]
        random.shuffle(ticket_code_parts)
        generated_ticket = ''.join(ticket_code_parts)
        
        # Store ticket information
        health_system.issued_tickets[generated_ticket] = {
            'initials': initials.upper(),
            'appointment_type': appointment_type,
            'severity': severity
        }
        health_system.ticket_counter += 1
        
        response = (f"Your appointment has been scheduled!\n"
                   f"Ticket: {generated_ticket}\n"
                   f"Appointment Type: {appointment_type}\n"
                   f"Severity Level: {severity}")
        
        dispatcher.utter_message(text=response)
        
        return [SlotSet("appointment_ticket", generated_ticket)]

class ActionCheckTicketStatus(Action):
    def name(self) -> Text:
        return "action_check_ticket_status"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        ticket_number = tracker.get_slot("ticket_number")
        if not ticket_number:
            dispatcher.utter_message(text="Please provide your ticket number to check its status.")
            return []
        
        health_system = HealthQuerySystem()
        ticket_info = health_system.issued_tickets.get(ticket_number)
        
        if ticket_info:
            response = (f"Ticket Status:\n"
                       f"Appointment Type: {ticket_info['appointment_type']}\n"
                       f"Patient Initials: {ticket_info['initials']}\n"
                       f"Severity Level: {ticket_info['severity']}")
            dispatcher.utter_message(text=response)
        else:
            dispatcher.utter_message(text="Sorry, I couldn't find any information for that ticket number. Please verify the number and try again.")
        
        return []

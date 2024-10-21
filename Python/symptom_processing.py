#Import statements and initial setup
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from fuzzywuzzy import fuzz, process
import json
import pyttsx3

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

#NLTK setup and preprocessing
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

#Loading and categorizing symptoms
json_file_path = '../datasets/JSON/severity_dict.json'
with open(json_file_path, 'r') as file:
    symptom_severity_dict = json.load(file)

CRITICAL_SYMPTOMS = symptom_severity_dict['CRITICAL_SYMPTOMS']
MINOR_SYMPTOMS = symptom_severity_dict['MINOR_SYMPTOMS']
AMBIGUOUS_SYMPTOMS = symptom_severity_dict['AMBIGUOUS_SYMPTOMS']
ALL_SYMPTOMS = {**CRITICAL_SYMPTOMS, **MINOR_SYMPTOMS, **AMBIGUOUS_SYMPTOMS}

#Loading Med-BERT model
model_name = "Charangan/MedBERT"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

#Caching mechanism for embeddings
embedding_cache = {}

#Sentence encoding function
def encode_sentence(sentence):
    if sentence not in embedding_cache:
        inputs = tokenizer(sentence, return_tensors="pt", padding=True, truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
        sentence_embedding = outputs.last_hidden_state.mean(dim=1).numpy()
        embedding_cache[sentence] = sentence_embedding
    return embedding_cache[sentence]

#Text preprocessing function
def preprocess_text(text):
    tokens = word_tokenize(text.lower())
    processed_tokens = [lemmatizer.lemmatize(token) for token in tokens if token not in stop_words]
    return processed_tokens

# Symptom detection function
def detect_symptoms_from_input(text, all_symptoms):
    processed_tokens = preprocess_text(text)
    detected_symptoms = []
    
    for symptom, variations in all_symptoms.items():
        for variation in variations:
            variation_tokens = preprocess_text(variation)
            if all(token in processed_tokens for token in variation_tokens):
                detected_symptoms.append(symptom)
                break
    
    return list(set(detected_symptoms))

#Batch sentence encoding function
def encode_sentences(sentences):
    inputs = tokenizer(sentences, return_tensors="pt", padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).numpy()

#Similarity calculation function
def calculate_similarity(user_input):
    input_embedding = encode_sentence(user_input)

    variations = [(variation, symptom) for symptom, variations in ALL_SYMPTOMS.items() for variation in variations]
    variations_texts = [variation[0] for variation in variations]
    
    variation_embeddings = encode_sentences(variations_texts)
    
    similarities = []
    for idx, (variation, symptom) in enumerate(variations):
        similarity = cosine_similarity(input_embedding, variation_embeddings[idx:idx + 1])[0][0]
        similarities.append((symptom, variation, similarity))

    similarities.sort(key=lambda x: x[2], reverse=True)
    return similarities

#Data loading function
def load_data(file_path):
    try:
        return pd.read_excel(file_path)
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return None
    except Exception as e:
        speak(f"An error occurred while loading data: {str(e)}")
        return None

#Fuzzy matching function for diseases
def find_top_diseases_fuzzy(symptoms, file_path, top_n=5):
    df = load_data(file_path)
    if df is None:
        return []

    matched_diseases = []
    for symptom in symptoms:
        for index, row in df.iterrows():
            spreadsheet_symptoms = row['Symptoms'].split(', ')
            best_match, score = process.extractOne(symptom, spreadsheet_symptoms, scorer=fuzz.token_sort_ratio)
            if score > 75:
                matched_diseases.append((row['Disease'], row['Symptoms'], best_match, score, row['Severity']))

    matched_diseases.sort(key=lambda x: x[3], reverse=True)
    return matched_diseases[:top_n]

#Direct match function
def find_direct_match(user_input):
    for symptom, variations in ALL_SYMPTOMS.items():
        if user_input in variations or user_input == symptom:
            return symptom
    return None

#Severity mapping and determination functions
def map_severity_string_to_score(severity_str):
    severity_mapping = {
        'Mild': 0.3,
        'Moderate': 0.6,
        'Severe': 0.9
    }
    return severity_mapping.get(severity_str, 0.0)

def determine_severity_level(severity_score):
    if severity_score <= 0.4:
        return "Mild"
    elif 0.4 < severity_score <= 0.7:
        return "Moderate"
    else:
        return "Severe"

def calculate_severity_based_on_category(symptoms):
    severity_score = 0
    for symptom in symptoms:
        if symptom in CRITICAL_SYMPTOMS:
            severity_score = max(severity_score, 0.9)
        elif symptom in AMBIGUOUS_SYMPTOMS:
            severity_score = max(severity_score, 0.7)
        elif symptom in MINOR_SYMPTOMS:
            severity_score = max(severity_score, 0.3)
    return severity_score

# Software Developer: Main processing function
def process_multiple_symptoms(initial_symptoms, file_path):
    speak(f"Processing the following symptoms: {initial_symptoms}")
    print(f"Processing the following symptoms: {initial_symptoms}")

    matched_symptoms = []
    for symptom in initial_symptoms:
        direct_match = find_direct_match(symptom.strip().lower())
        if direct_match:
            matched_symptoms.append(direct_match)
            speak(f"Direct match found: {direct_match} for '{symptom}'")
        else:
            similarities = calculate_similarity(symptom.strip().lower())
            best_match = similarities[0][0] if similarities else None
            if best_match:
                matched_symptoms.append(best_match)
                speak(f"No direct match for '{symptom}'. Best match found using BERT: {best_match}")
            else:
                speak(f"No match found for '{symptom}'.")

    top_diseases = find_top_diseases_fuzzy(matched_symptoms, file_path)
    
    if top_diseases:
        top_disease_severity = top_diseases[0][4]
        severity_score = map_severity_string_to_score(top_disease_severity)
        severity_level = determine_severity_level(severity_score)
        speak(f"Severity of the top disease: {severity_level}")
        print(f"Severity of the disease is: {severity_level}")

        return matched_symptoms, severity_level, top_diseases
    else:
        speak("No matching diseases found. Estimating severity based on symptom category.")
        estimated_severity_score = calculate_severity_based_on_category(matched_symptoms)
        severity_level = determine_severity_level(severity_score=estimated_severity_score)
        speak(f"Estimated severity based on symptom category is: {severity_level}")
        print(f"Your severity is:{severity_level}")

        return matched_symptoms, severity_level, []

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


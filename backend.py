from groq import Groq
import base64
from dotenv import load_dotenv
import os
import json

class ExpenseAgent : 
    def __init__(self):
        load_dotenv()
        self.client = Groq(api_key=os.environ["GROQ_API_KEY"])

    @staticmethod
    def read_file(file_path):
        with open(file_path, "r") as file:
            return file.read()
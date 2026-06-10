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
    
    def extract_from_bytes(self, image_bytes: bytes, media_type: str = "image/jpeg") -> dict:
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        base_dir = os.path.dirname(os.path.abspath(__file__))

        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": ExpenseAgent.read_file(os.path.join(base_dir, "context.txt"))
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": ExpenseAgent.read_file(os.path.join(base_dir, "prompt.txt"))
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            response_format={"type": "json_object"},
            model="meta-llama/llama-4-scout-17b-16e-instruct"
        )

        result = json.loads(chat_completion.choices[0].message.content)

        expected_fields = [
            "type_document", "fournisseur", "date", "montant_ttc",
            "tva", "devise", "description", "confiance"
        ]
        for field in expected_fields:
            if field not in result:
                result[field] = None

        return result


if __name__ == "__main__":
    agent = ExpenseAgent()

    image_path = "ticket.jpg"

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    result = agent.extract_from_bytes(image_bytes)
    print(result)



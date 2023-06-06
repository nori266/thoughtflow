import os
import re
from typing import Dict, Union

from dotenv import load_dotenv
import openai

load_dotenv()

openai.api_key = os.getenv("API_KEY_OPENAI")
model_id_only_label = os.getenv("MODEL_ID")
model_id_all_fields = os.getenv("MODEL_ID_ALL_FIELDS")


class GPTClassifier:
    @staticmethod
    def predict(message: str) -> Dict[str, str]:
        if re.sub(r'https?://\S+', "", message).strip() == "":
            return {"category": "link"}
        prompt = f"Note: {message} "
        response = openai.Completion.create(
            engine=model_id_only_label,
            prompt=prompt,
            max_tokens=10,
            # TODO test with lower temperature
            temperature=0.9,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["\n"]
        )
        prediction = response["choices"][0]["text"]
        return GPTClassifier.post_process_prediction(prediction)

    @staticmethod
    def post_process_prediction(prediction: str) -> Dict[str, str]:
        PREDICTION_PATTERN = re.compile(r'Category: ([a-z]+)_')
        match = PREDICTION_PATTERN.search(prediction)
        category = match.group(1) if match else "unknown"
        if category == "pet":
            category = "pet_project"
        return {"category": category}


class GPTAllFieldsGenerator:
    @staticmethod
    def predict(message: str) -> Dict[str, Union[str, float]]:
        if re.sub(r'https?://\S+', "", message).strip() == "":
            return {
            "category": "link",
            "action": "todo",
            "urgency": "unknown",
            "eta": None
        }
        prompt = f"Note: {message} "
        response = openai.Completion.create(
            engine=model_id_all_fields,
            prompt=prompt,
            max_tokens=30,
            temperature=0,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["\n"]
        )
        prediction = response["choices"][0]["text"]
        return GPTAllFieldsGenerator.post_process_prediction(prediction)

    @staticmethod
    def post_process_prediction(prediction_text: str) -> Dict[str, Union[str, float]]:
        PREDICTION_PATTERN = re.compile(r'Category: ([a-z_]+),')
        ACTION_PATTERN = re.compile(r'Action: ([a-z]+),')
        URGENCY_PATTERN = re.compile(r'Urgency: ([a-z]+),')
        ETA_PATTERN = re.compile(r'ETA: ([0-9.]+),')
        match = PREDICTION_PATTERN.search(prediction_text)
        category = match.group(1) if match else "unknown"
        if category == "pet":
            category = "pet_project"

        match = ACTION_PATTERN.search(prediction_text)
        action = match.group(1) if match else "unknown"

        match = URGENCY_PATTERN.search(prediction_text)
        urgency = match.group(1) if match else "unknown"

        match = ETA_PATTERN.search(prediction_text)
        eta = match.group(1) if match else None

        return {
            "category": category,
            "action": action,
            "urgency": urgency,
            "eta": eta
        }


if __name__ == '__main__':
    # TODO add to tests
    message = "build ui for a pet project"
    print(GPTClassifier.predict(message))

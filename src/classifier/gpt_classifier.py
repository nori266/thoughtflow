import os
import re

from dotenv import load_dotenv
import openai

load_dotenv()

openai.api_key = os.getenv("API_KEY_OPENAI")
model_id = os.getenv("MODEL_ID")

PREDICTION_PATTERN = re.compile(r'Category: ([a-z]+)_')


class GPTClassifier:
    @staticmethod
    def predict(message: str) -> str:
        prompt = f"Note: {message} "
        response = openai.Completion.create(
            engine=model_id,
            prompt=prompt,
            max_tokens=10,
            temperature=0.9,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["\n"]
        )
        prediction = response["choices"][0]["text"]
        match = PREDICTION_PATTERN.search(prediction)
        category = match.group(1) if match else "unknown"
        return category


if __name__ == '__main__':
    # TODO add to tests
    message = "find good films by a director of Call me by your name"
    print(GPTClassifier.predict(prompt))

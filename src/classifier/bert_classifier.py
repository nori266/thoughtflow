import logging
import numpy as np
from pathlib import Path
import sys
from typing import List

from dotenv import load_dotenv
from sklearn.preprocessing import LabelEncoder
import torch
from transformers import BertTokenizer, BertForSequenceClassification, Trainer

sys.path.append(str(Path(__file__).parent))

from classifier.dataset import ThoughtDataset

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level = logging.DEBUG)


class BertClassifier:
    def __init__(self, model_path: str):
        self.encoder = LabelEncoder()
        self.encoder.classes_ = np.load((Path(model_path).parent / 'label_encoding.npy').as_posix())
        self.model = BertForSequenceClassification.from_pretrained(model_path)
        self.tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
        self.trainer = Trainer(model=self.model)

    def predict(self, texts: List[str]) -> (List[str], List[float]):
        if isinstance(texts, str):
            texts = [texts]
        test_encodings = self.tokenizer(texts, truncation=True, padding=True, max_length=64)
        dataset = ThoughtDataset(test_encodings)
        raw_pred, _, _ = self.trainer.predict(dataset)
        probabilities = torch.softmax(torch.tensor(raw_pred), dim=1)
        logger.warning("Model predictions: %s", probabilities)
        best_scores, y_pred = probabilities.topk(1, dim=1)
        best_scores = best_scores.detach().numpy().squeeze()
        predictions = self.encoder.inverse_transform(y_pred)
        # return predictions, best_scores
        return predictions[0]

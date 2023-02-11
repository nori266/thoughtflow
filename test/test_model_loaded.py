import logging
from pathlib import Path
import sys

import torch
from transformers import BertTokenizer, BertForSequenceClassification, Trainer

sys.path.append(str(Path(__file__).parent.parent))

from classifier.dataset import ThoughtDataset

logger = logging.getLogger(__name__)
logging.basicConfig(level = logging.DEBUG)


if __name__ == '__main__':
    texts = ["test note 1", "test note 2", "test note 3"]
    tokenizer = BertTokenizer.from_pretrained("models/bert-base-uncased")
    model = BertForSequenceClassification.from_pretrained("models/fine_tuned_bert/230126_test_model/checkpoint-187")
    test_trainer = Trainer(model=model)
    test_encodings = tokenizer(texts, truncation=True, padding=True, max_length=64)
    dataset = ThoughtDataset(test_encodings)
    raw_pred, _, _ = test_trainer.predict(dataset)
    probabilities = torch.softmax(torch.tensor(raw_pred), dim=1)
    logger.warning("Model predictions: %s", probabilities)

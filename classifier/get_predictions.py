import configparser
import argparse

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
import torch
from transformers import BertTokenizer, BertForSequenceClassification, Trainer

from dataset import ThoughtDataset


def calculate_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    return {
        'accuracy': accuracy_score(labels, predictions)
    }


def get_predictions(texts, tokenizer, model):
    dataset = ThoughtDataset(texts, tokenizer)
    predictions = model.predict(dataset)
    return np.argmax(predictions[0], axis=1)


def main(config: configparser.ConfigParser):
    if config.has_option("PARAM", "label_column"):
        label_column = config["PARAM"]["label_column"]
    else:
        label_column = "class"

    data = pd.read_csv(config['FILE']['test_data'])
    texts = data["thought"].tolist()
    labels = data[label_column].tolist()

    encoder = LabelEncoder()
    encoder.classes_ = np.load('label_encoding.npy')
    print(encoder.classes_, len(encoder.classes_))

    trained_model = config['FILE']['trained_model']
    base_model_path = config['FILE']['base_model']
    max_seq_length = int(config['PARAM']['max_seq_length'])

    tokenizer = BertTokenizer.from_pretrained(base_model_path)
    model = BertForSequenceClassification.from_pretrained(trained_model)

    test_trainer = Trainer(model=model)
    test_encodings = tokenizer(texts, truncation=True, padding=True, max_length=max_seq_length)
    dataset = ThoughtDataset(test_encodings)
    raw_pred, _, _ = test_trainer.predict(dataset)
    probabilities = torch.softmax(torch.tensor(raw_pred), dim=1)
    best_scores, y_pred = probabilities.topk(1, dim=1)
    best_scores = best_scores.detach().numpy().squeeze()
    predictions = encoder.inverse_transform(y_pred)
    print(predictions)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, help="Path to config file")
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.config)

    main(config)

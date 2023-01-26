import argparse
import configparser
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
from sklearn.utils import shuffle
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments

from dataset import ThoughtDataset


"""
Fine-tuning BERT for text classification with the data from the csv file.
"""


def calculate_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    return {
        'accuracy': accuracy_score(labels, predictions)
    }


def main(config: configparser.ConfigParser):
    # data = db.get_class_train_data()
    train_data = shuffle(pd.read_csv(config['FILE']['train_data']))
    test_data = shuffle(pd.read_csv(config['FILE']['test_data']))
    model_out_path = Path(config['FILE']['model_out'])
    base_model_path = config['FILE']['base_model']

    model_out_path.mkdir(parents=True, exist_ok=True)

    if config.has_option("PARAM", "label_column"):
        label_column = config["PARAM"]["label_column"]
    else:
        label_column = "label"

    train_texts = train_data["thought"].tolist()
    test_texts = test_data["thought"].tolist()

    train_labels = train_data[label_column].tolist()
    test_labels = test_data[label_column].tolist()

    le = LabelEncoder()
    train_labels_bin = le.fit_transform(train_labels)
    # save the label encoder

    np.save((model_out_path / 'label_encoding.npy').as_posix(), le.classes_)
    test_labels_bin = le.transform(test_labels)
    num_labels = len(le.classes_)

    tokenizer = BertTokenizer.from_pretrained(base_model_path)
    model = BertForSequenceClassification.from_pretrained(base_model_path, num_labels=num_labels)

    max_seq_length = int(config['PARAM']['max_seq_length'])
    epochs = int(config['PARAM']['epochs'])
    batch_size = int(config['PARAM']['batch_size'])
    learning_rate = float(config['PARAM']['learning_rate'])

    print("Steps per epoch:", len(train_texts) // batch_size)

    train_encodings = tokenizer(train_texts, truncation=True, padding=True, max_length=max_seq_length)
    test_encodings = tokenizer(test_texts, truncation=True, padding=True, max_length=max_seq_length)
    train_dataset = ThoughtDataset(train_encodings, train_labels_bin)
    test_dataset = ThoughtDataset(test_encodings, test_labels_bin)

    training_args = TrainingArguments(
        output_dir=model_out_path.as_posix(),                  # output directory
        num_train_epochs=epochs,                    # total # of training epochs
        per_device_train_batch_size=batch_size,     # batch size per device during training
        per_device_eval_batch_size=batch_size,      # batch size for evaluation
        evaluation_strategy="epoch",                # evaluation strategy to adopt during training
        save_strategy="epoch",                      # model saving strategy
        learning_rate=learning_rate,                # learning rate
        seed=0,                                     # random seed for initialization
        load_best_model_at_end=True,                # load best model at the end of training
        save_total_limit=3,                         # number of total saved models
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        compute_metrics=calculate_metrics,
    )
    if config.has_option("FILE", "continue_from"):
        checkpoint = config["FILE"]["continue_from"]
        print("Continue training from", checkpoint)
        trainer.train(resume_from_checkpoint=checkpoint)
    else:
        print("Training from scratch")
        trainer.train()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, help='Path to config file')
    args = parser.parse_args()
    config = configparser.ConfigParser()
    config.read(args.config)
    main(config)

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

import torch
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments

import db_operations as db

"""
Fine-tuning BERT for text classification with the data from the csv file.
"""

# model.save_pretrained('models/bert-base-uncased')
# tokenizer.save_pretrained('models/bert-base-uncased')


class ThoughtDataset(torch.utils.data.Dataset):
    def __init__(self, encoding, labels):
        self.encoding = encoding
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encoding.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)


# data = db.get_class_train_data()
data = pd.read_csv('data/my_showcase_data.csv')
train, test = train_test_split(data, test_size=0.1, random_state=0)
train_labels = train['class'].tolist()
test_labels = test['class'].tolist()

le = LabelEncoder()
train_labels_bin = le.fit_transform(train_labels)
test_labels_bin = le.transform(test_labels)
num_labels = len(le.classes_)

tokenizer = BertTokenizer.from_pretrained('models/bert-base-uncased')
model = BertForSequenceClassification.from_pretrained("models/bert-base-uncased", num_labels=num_labels)
train_encodings = tokenizer(train['thought'].tolist(), truncation=True, padding=True, max_length=128)
test_encodings = tokenizer(test['thought'].tolist(), truncation=True, padding=True, max_length=128)
train_dataset = ThoughtDataset(train_encodings, train_labels_bin)
test_dataset = ThoughtDataset(test_encodings, test_labels_bin)

training_args = TrainingArguments(
    output_dir='models/fine_tuned_bert',          # output directory
    num_train_epochs=3,              # total # of training epochs
    per_device_train_batch_size=16,  # batch size per device during training
    per_device_eval_batch_size=16,   # batch size for evaluation
    logging_steps=10,
)


trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
)

trainer.train()

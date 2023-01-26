import datetime

import pandas as pd
from sklearn.model_selection import train_test_split

"""
1. Split train/test data
2. Leave only the relevant columns
"""

data = pd.read_csv('data/all_thoughts.csv')
train, test = train_test_split(data, test_size=0.1, random_state=0)

now = datetime.datetime.now()
date = now.strftime("%y%m%d")

train[["thought", "label"]].to_csv(f'data/train_test_data/{date}_train.csv', index=False)
test[["thought", "label"]].to_csv(f'data/train_test_data/{date}_test.csv', index=False)

print("Train data shape:", train.shape)
print("Test data shape:", test.shape)

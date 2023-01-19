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
date = now.strftime("%Y-%m-%d")

train[["thought", "class"]].to_csv(f'data/{date}_train.csv', index=False)
test[["thought", "class"]].to_csv(f'data/{date}_test.csv', index=False)

"""
Basic functionality:
- push a random note with the status "open"
- ask if it's still relevant
- give possibility to change the status
"""

import pandas as pd

RELEVANT_FILES = [
    "thoughts.csv",
    "thoughts_with_eta.csv",
    "thoughts_from_work.csv",
    "thoughts_with_all_fields.csv",
]


def get_random_note():
    df = pd.concat([pd.read_csv(f)[["thought", "class", "status"]] for f in RELEVANT_FILES])
    df = df[df.status == "open"]
    return df.sample(1).values

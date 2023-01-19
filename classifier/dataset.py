import torch


class ThoughtDataset(torch.utils.data.Dataset):
    def __init__(self, encoding, labels=None):
        self.encoding = encoding
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encoding.items()}
        if self.labels is not None:
            item["labels"] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.encoding.input_ids)

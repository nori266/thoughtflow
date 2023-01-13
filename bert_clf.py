from transformers import BertTokenizer, BertModel

# tokenizer = BertTokenizer.from_pretrained('models/bert-base-uncased')
model = BertModel.from_pretrained("models/bert-base-uncased")
# model.save_pretrained('models/bert-base-uncased')

# trainer = Trainer(
#     model=model,
#     args=training_args,
#     train_dataset=train_dataset,
#     eval_dataset=eval_dataset,
#     compute_metrics=compute_metrics
# )
#
# trainer.train()

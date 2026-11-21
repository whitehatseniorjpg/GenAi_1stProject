from datasets import load_dataset
from transformers import (
    BertConfig,
    BertForMaskedLM,
    BertTokenizerFast,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments
)
print("Loading Dataset")
raw_dataset = load_dataset("HuggingFaceTB/cosmopedia","khanacademy",split="train")

tokenizer = BertTokenizerFast.from_pretrained("bert-base-uncased")

config = BertConfig(
    vocab_size=len(tokenizer),
    hidden_size=128,
    num_hidden_layers=4,
    num_attention_heads=4,
    intermediate_size=512,
    max_position_embeddings=128,
    pad_token_id=tokenizer.pad_token_id
)

model = BertForMaskedLM(config)

def tokenize_function(example):
    return tokenizer(
        example["text"],
        truncation=True,
        max_length=128,
        padding="max_length"
    )

MODEL_DIR = "./llm_encoder_model"
small_dataset = raw_dataset.select(range(10000))
tokenized_dataset = small_dataset.map(
    tokenize_function,
    batched=True,
    remove_columns=["text"]
)

training_args = TrainingArguments(
    output_dir=MODEL_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=8,
    save_steps=500,
    logging_steps=50,
    learning_rate=5e-4
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=True,
        mlm_probability=0.15
    )
)

trainer.train()

model.save_pretrained(MODEL_DIR)
tokenizer.save_pretrained(MODEL_DIR)
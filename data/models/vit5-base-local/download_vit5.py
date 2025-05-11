from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

model_name = "VietAI/vit5-base"
local_dir = "./vit5-base-local"

# Thêm from_tf=True để load trọng số từ TensorFlow
model = AutoModelForSeq2SeqLM.from_pretrained(model_name, from_tf=True)
tokenizer = AutoTokenizer.from_pretrained(model_name)

model.save_pretrained(local_dir)
tokenizer.save_pretrained(local_dir)

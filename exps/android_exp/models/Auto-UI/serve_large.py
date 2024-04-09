import os
import numpy as np
import torch
import os
import re
import json
import argparse
import random
from transformers import AutoTokenizer, DataCollatorForSeq2Seq, Seq2SeqTrainingArguments, Seq2SeqTrainer
from model import T5ForMultimodalGeneration
from infer_utils import ImageFeatureExtractor
from PIL import Image

img_dim = 1408
model_path = "/home/jiayipan/code/ICML_GUI/Auto-UI/weights/Auto-UI-Large"
model = T5ForMultimodalGeneration.from_pretrained(model_path, img_dim).cuda()
tokenizer = AutoTokenizer.from_pretrained(model_path)
img_extractor = ImageFeatureExtractor()

def generate(text: str, imgage: Image):
    inputs = tokenizer(text, return_tensors="pt")
    img_feat = img_extractor.to_feat(imgage)
    img_feat = img_feat.float().cuda()
    out = model.generate(
        input_ids = inputs["input_ids"].to("cuda"),
        attention_mask = inputs["attention_mask"].to("cuda"),
        image_ids = img_feat.unsqueeze(0).to("cuda"),
        max_length=128,
    )
    text = tokenizer.decode(out[0], skip_special_tokens=True)
    return text


import gradio as gr

def main():
    demo = gr.Interface(
        fn=generate,
        inputs=["textbox", "image"],
        outputs="text")
    demo.launch(share=True)

if __name__ == "__main__":
    main()
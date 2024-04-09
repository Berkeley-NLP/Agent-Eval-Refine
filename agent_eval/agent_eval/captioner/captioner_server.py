from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    __version__,
    GenerationConfig,
)
from PIL import Image
import gradio as gr
import argparse
import tempfile

from PIL import Image
import easyocr
import torch

assert (
    __version__ == "4.32.0"
), "Please use transformers version 4.32.0, pip install transformers==4.32.0"

reader = easyocr.Reader(
    ["en"]
)  # this needs to run only once to load the model into memory


def get_easy_text(img_file):
    out = reader.readtext(img_file, detail=0, paragraph=True)
    if isinstance(out, list):
        return "\n".join(out)
    return out

model_name = "DigitalAgent/Captioner"
if torch.cuda.is_available():
    device = torch.device("cuda")
else:
    device = torch.device("cpu")
model = (
    AutoModelForCausalLM.from_pretrained(
        model_name, trust_remote_code=True
    ).to(device)
    .eval()
    .half()
)
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
generation_config = GenerationConfig.from_dict(
    {
        "chat_format": "chatml",
        "do_sample": True,
        "eos_token_id": 151643,
        "max_new_tokens": 2048,
        "max_window_size": 6144,
        "pad_token_id": 151643,
        "repetition_penalty": 1.2,
        "top_k": 0,
        "top_p": 0.3,
        "transformers_version": "4.31.0",
    }
)


def generate(image: Image):
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as tmp:
        image.save(tmp.name)
        ocr_result = get_easy_text(tmp.name)
        text = f"Please describe the screenshot above in details.\nOCR Result:\n{ocr_result}"
        history = []
        input_data = [{"image": tmp.name}, {"text": text}]
        query = tokenizer.from_list_format(input_data)
        response, _ = model.chat(
            tokenizer, query=query, history=history, generation_config=generation_config
        )
        return response


def main(port, share):
    demo = gr.Interface(
        fn=generate, inputs=[gr.Image(type="pil")], outputs="text", concurrency_limit=1
    )
    demo.queue().launch(server_port=port, share=share)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int)
    parser.add_argument("--share", action="store_true", default=False)
    args = parser.parse_args()
    main(args.port, args.share)

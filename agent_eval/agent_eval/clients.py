import openai
from openai.api_resources import ChatCompletion

# from openai import OpenAI, AsyncOpenAI
import requests
from typing import List, Union, Dict, Optional, Tuple
from PIL import Image
from io import BytesIO
import base64

# from openai.types.chat.chat_completion import ChatCompletion
import os
import requests
import json
import numpy as np


def query_anyscale_api(messages, model, temperature=0):
    # Set the base URL and API key for the OpenAI API
    try:
        base_url = "https://api.endpoints.anyscale.com/v1"
        api_key = "esecret_xv1c6k71xizxxpxed457wgwlib"

        # Endpoint for chat completions
        url = f"{base_url}/chat/completions"

        # Headers for the request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        # Data payload for the request
        data = {"model": model, "messages": messages, "temperature": temperature}

        # Make the POST request and return the response
        response = requests.post(url, headers=headers, data=json.dumps(data)).json()
        return response["choices"][0]["message"]["content"].lstrip(), response
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        print(traceback.format_exc())
        return f"API_ERROR: {e}", None

def query_openai_api(messages, model, temperature=0, api_key=None):
    try:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        data = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": 4096}

        # Make the POST request and return the response
        response = requests.post(url, headers=headers, data=json.dumps(data)).json()
        # return response
        from pprint import pprint
        return response["choices"][0]["message"]["content"].lstrip(), response
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"API_ERROR: {e}", None
    
#     curl https://api.openai.com/v1/chat/completions \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer $OPENAI_API_KEY" \
#   -d '{
#     "model": "gpt-4-vision-preview",
#     "messages": [
#       {
#         "role": "user",
#         "content": [
#           {
#             "type": "text",
#             "text": "What’s in this image?"
#           },
#           {
#             "type": "image_url",
#             "image_url": {
#               "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
#             }
#           }
#         ]
#       }
#     ],
#     "max_tokens": 300
#   }'



class LM_Client:
    def __init__(self, api_key, model_name="local"):
        # self.client = OpenAI(api_key=api_key)
        if model_name == "local":
            # TODO: The 'openai.api_base' option isn't read in the client API. You will need to pass it when you instantiate the client, e.g. 'OpenAI(api_base="http://localhost:8082/v1")'
            # openai.api_base = "http://localhost:8082/v1"
            models = self.client.models.list()
            model = models["data"][0]["id"]
            self.model = model
        elif model_name == "gpt-3.5":
            # self.model = "gpt-3.5-turbo-1106"
            self.model = "gpt-3.5-turbo"
            openai.api_key = os.environ["OPENAI_API_KEY"]
            openai.organization = os.environ.get("OPENAI_ORGANIZATION", "")
        elif model_name == "gpt-4":
            self.model = "gpt-4-1106-preview"
            openai.api_key = os.environ["OPENAI_API_KEY"]
            openai.organization = os.environ.get("OPENAI_ORGANIZATION", "")
        elif model_name == "mixtral":
            self.model = "mistralai/Mixtral-8x7B-Instruct-v0.1"
            # openai.api_key = "esecret_xv1c6k71xizxxpxed457wgwlib"
            # openai.base_url = "https://api.endpoints.anyscale.com/v1"
            # self.client = OpenAI(
            #     base_url = "https://api.endpoints.anyscale.com/v1",
            #     api_key="esecret_xv1c6k71xizxxpxed457wgwlib",
            # )
        else:
            raise ValueError(f"Invalid model name: {model_name}")

    def chat(self, messages, json_mode=False) -> Tuple[str, ChatCompletion]:
        """
        messages=[{
            "role": "system",
            "content": "You are a helpful assistant."
        }, {
            "role": "user",
            "content": "hi"}
        ])
        """
        if "mistral" in self.model:
            model = "mistralai/Mixtral-8x7B-Instruct-v0.1"
            response_str, chat_completion = query_anyscale_api(messages, self.model)
        else:
            chat_completion = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"} if json_mode else None,
                temperature=0,
            )
            response_str = chat_completion["choices"][0]["message"]["content"]
        return response_str, chat_completion

    def one_step_chat(
        self, text, system_msg: Optional[str] = None, json_mode=False
    ) -> Tuple[str, ChatCompletion]:
        messages = []
        if system_msg is not None:
            messages.append({"role": "system", "content": system_msg})
        messages.append({"role": "user", "content": text})
        return self.chat(messages, json_mode=json_mode)


class VLM_Client:
    def __init__(self, port=8083) -> None:
        self.url = f"http://localhost:{port}"

    def chat(self, data: List[Dict[str, Union[str, None]]]) -> str:
        """
        Send a request to the FastAPI service and get the model's response.
            data = [
                [
                    {'image': 'https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen-VL/assets/demo.jpeg'},
                    {'text': "What is it?"},
                ],
            ]

        :param data: List of dictionaries with keys "image" and/or "text"
        :return: Model's response as a string
        """
        response = requests.post(f"{self.url}/get_response/", json=data)

        # Check if the request was successful
        if response.status_code == 200:
            return response.json()["response"]
        else:
            raise Exception(
                f"Error with status code {response.status_code}: {response.text}"
            )

    def one_step_chat(self, img, text) -> str:
        data = [[{"image": img}, {"text": text}]]
        return self.chat(data)


class GPT4V_Client:
    def __init__(self, api_key, model_name="gpt-4-vision-preview", max_tokens=512):
        self.api_key = api_key
        # self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        self.max_tokens = max_tokens

    def chat(self, messages, json_mode=False) -> Tuple[str, ChatCompletion]:
        return query_openai_api(messages, self.model_name, api_key=self.api_key)

    def one_step_chat(
        self, text, image: Union[Image.Image, np.ndarray], system_msg: Optional[str] = None, json_mode=False
    ) -> Tuple[str, ChatCompletion]:
        jpeg_buffer = BytesIO()

        # Save the image as JPEG to the buffer
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        image = image.convert("RGB")
        image.save(jpeg_buffer, format="JPEG")

        # Get the byte data from the buffer
        jpeg_data = jpeg_buffer.getvalue()

        # Encode the JPEG image data in base64
        jpg_base64 = base64.b64encode(jpeg_data)

        # If you need it in string format
        jpg_base64_str = jpg_base64.decode("utf-8")
        messages = []
        if system_msg is not None:
            messages.append({"role": "system", "content": system_msg})
        messages += [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{jpg_base64_str}"
                        },
                    },
                ],
            }
        ]
        return self.chat(messages, json_mode=json_mode)

    def one_step_multi_image_chat(
        self, text, images: list[Union[Image.Image, np.ndarray]], system_msg: Optional[str] = None, json_mode=False
    ) -> Tuple[str, ChatCompletion]:
        """
        images: [{"image": PIL.image, "detail": "high" or "low }]

        For low res mode, we expect a 512px x 512px image. For high res mode, the short side of the image should be less than 768px and the long side should be less than 2,000px.
        """
        details = [i["detail"] for i in images]
        img_strs = []
        for img_info in images:
            image = img_info["image"]
            jpeg_buffer = BytesIO()

            # Save the image as JPEG to the buffer
            if isinstance(image, np.ndarray):
                image = Image.fromarray(image)
            image = image.convert("RGB")
            image.save(jpeg_buffer, format="JPEG")

            # Get the byte data from the buffer
            jpeg_data = jpeg_buffer.getvalue()

            # Encode the JPEG image data in base64
            jpg_base64 = base64.b64encode(jpeg_data)

            # If you need it in string format
            jpg_base64_str = jpg_base64.decode("utf-8")
            img_strs.append(f"data:image/jpeg;base64,{jpg_base64_str}")
        messages = []
        if system_msg is not None:
            messages.append({"role": "system", "content": system_msg})

        img_sub_msg = [
            {
                "type": "image_url",
                "image_url": {"url": img_str, "detail": detail},
            }
            for img_str, detail in zip(img_strs, details)
        ]
        messages += [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text},
                ]
                + img_sub_msg,
            }
        ]
        return self.chat(messages, json_mode=json_mode)


# class BatchGPT4V:
#     def __init__(self, api_key, model_name="gpt-4-vision-preview", max_tokens=512):
#         self.client = AsyncOpenAI(api_key=api_key)
#         self.model_name = model_name
#         self.max_tokens = max_tokens

#     async def one_step_chat(
#         self, text, image: Image, system_msg: Optional[str] = None, json_mode=False
#     ):

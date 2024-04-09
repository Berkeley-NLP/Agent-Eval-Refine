from setuptools import setup

setup(
    name="agent_eval",
    version="0.0.1",
    packages=["agent_eval"],
    install_requires=[
        "openai",
        "requests",
        "pillow",
        "bs4",
        "matplotlib",
        "termcolor",
        "human_id",
        "pandas",
        "easy_ocr",
        "einops",
        "transformers_stream_generator",
        "tiktoken"
    ]
)

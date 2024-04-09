import torch
from PIL import Image
from transformers import AutoProcessor, Blip2Model, AutoTokenizer
from model import T5ForMultimodalGeneration

class ImageFeatureExtractor:
    def __init__(self):
        # Set device based on CUDA availability
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Initialize and load the BLIP2 model and processor
        self.model = Blip2Model.from_pretrained("Salesforce/blip2-opt-2.7b").to(self.device)
        self.processor = AutoProcessor.from_pretrained("Salesforce/blip2-opt-2.7b")

    def to_feat(self, image: Image.Image):
        """Converts a PIL image to a feature representation using the BLIP2 model.
        
        Args:
            image: A PIL.Image object representing the image to convert.
            
        Returns:
            A tensor representing the image feature.
        """
        with torch.no_grad():
            # Preprocess the image and move to the correct device
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            
            # Get the image features from the model
            image_features = self.model.get_image_features(**inputs).pooler_output[0]
            
            # Detach the tensor from the graph and move it to CPU
            image_features = image_features.detach().cpu()
            
        return image_features

class AutoUI:
    def __init__(self):
        # Initialize the image feature extractor
        img_dim = 1408
        model_path = "/home/jiayipan/code/ICML_GUI/Auto-UI/weights/Auto-UI-Base"
        self.image_feature_extractor = ImageFeatureExtractor()
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = T5ForMultimodalGeneration.from_pretrained(model_path, img_dim) 
    
    def generate(self, image: Image.Image, text: str):
        # Convert the image to a feature representation
        image_features = self.image_feature_extractor.to_feat(image)
        
        # Encode the text
        inputs = self.tokenizer(text, return_tensors="pt")
        
        # Generate the output
        outputs = self.model.generate(
            input_ids=inputs["input_ids"].to(self.model.device),
            attention_mask=inputs["attention_mask"].to(self.model.device),
            image_features=image_features.unsqueeze(0).to(self.model.device),
            max_length=128,
            num_beams=4,
            early_stopping=True,
            do_sample=True,
            top_k=50,
            top_p=0.95,
            temperature=1.0,
            num_return_sequences=1,
            decoder_start_token_id=self.tokenizer.pad_token_id,
        )
        
        # Decode the output
        return self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
    
from enum import Enum
from dataclasses import dataclass
from typing import Tuple

class ActionType(Enum):
    Idle=0
    DualPoint=1
    Type=2
    GoBack=3
    GoHome=4
    Enter=5
    TaskComplete=6
    TaskImpossible=7

@dataclass
class AndroidAction():
    action_type: ActionType
    touch_point: Tuple[float, float] = None
    lift_point: Tuple[float, float] = None
    typed_text: str = None

    def __str__(self):
        # Construct the basic action type string.
        components = [f"Action Type: {self.action_type.name}"]

        # Format and add touch_point if it's not None.
        if self.touch_point:
            touch_point_str = f"({self.touch_point[0]:.4f}, {self.touch_point[1]:.4f})"
            components.append(f"Touch Point: {touch_point_str}")

        # Format and add lift_point if it's not None.
        if self.lift_point:
            lift_point_str = f"({self.lift_point[0]:.4f}, {self.lift_point[1]:.4f})"
            components.append(f"Lift Point: {lift_point_str}")

        # Add typed_text if it's not None.
        if self.typed_text:
            components.append(f"Typed Text: '{self.typed_text}'")

        # Join all components into a single string.
        return ", ".join(components)

    def to_act(self):
        pass

    def to_autoui(self):
        if self.action_type == ActionType.DualPoint:
            return f'"action_type": "DUAL_POINT", "touch_point": "[{self.touch_point[0]:.4f}, {self.touch_point[1]:.4f}]", "lift_point": "[{self.lift_point[0]:.4f}, {self.lift_point[0]:.4f}]", "typed_text": ""'
        elif self.action_type == ActionType.Type:
            return f'"action_type": "TYPE", "touch_point": "[-1.0, -1.0]", "lift_point": "[-1.0, -1.0]", "typed_text": "{self.typed_text}"'
        elif self.action_type == ActionType.GoBack:
            return f'"action_type": "PRESS_BACK", "touch_point": "[-1.0, -1.0]", "lift_point": "[-1.0, -1.0]", "typed_text": ""'
        elif self.action_type == ActionType.GoHome:
            return f'"action_type": "PRESS_HOME", "touch_point": "[-1.0, -1.0]", "lift_point": "[-1.0, -1.0]", "typed_text": ""'
        elif self.action_type == ActionType.Enter:
            return f'"action_type": "PRESS_ENTER", "touch_point": "[-1.0, -1.0]", "lift_point": "[-1.0, -1.0]", "typed_text": ""'
        elif self.action_type == ActionType.TaskComplete or self.action_type == ActionType.TaskImpossible:
            return f'"action_type": "TASK_COMPLETE", "touch_point": "[-1.0, -1.0]", "lift_point": "[-1.0, -1.0]", "typed_text": ""'

def format_prompt(history, goal):
    prompt = "Previous Actions: "
    for act in history:
        prompt += f"{act.to_autoui()} "
    prompt += f"Goal: {goal}</s>"
    return prompt
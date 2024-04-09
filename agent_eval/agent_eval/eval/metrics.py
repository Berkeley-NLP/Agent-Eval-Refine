import os
import json
import pandas as pd


LABEL_CORRECTION = {
    "24": False,
    "201": False,
    "225": False,
    "247": False,
    "390": False,
    "435": False,
    "466": False,
    "677": False,
    "678": False,
    "679": False,
    "680": False,
    "752": False,
    "792": False,
    "793": False,
}

def calculate_performance(dataframe):
    # Initialize the counts
    TP = FP = TN = FN = 0
    # Iterate through each column (each category)
    for column in dataframe.columns:
        gt, rm = dataframe[column]

        if gt and rm:
            TP += 1
        elif not gt and not rm:
            TN += 1
        elif not gt and rm:
            FP += 1
        elif gt and not rm:
            FN += 1
    return TP, FP, TN, FN



def get_metrics_from_result_json(result_json_path):
    data = pd.read_json(result_json_path)
    # Calculate the performance metrics
    classification_dict = {"TP": [], "TN": [], "FP": [], "FN": []}
    with open(result_json_path, "r") as json_file:
        json_data = json.load(json_file)
    # Classify each entry
    for key, values in json_data.items():

        gt = values["gt"]
        if key in LABEL_CORRECTION:
            gt = LABEL_CORRECTION[key]

        if gt and values["rm"]:
            classification_dict["TP"].append(key)
        elif not gt and not values["rm"]:
            classification_dict["TN"].append(key)
        elif not gt and values["rm"]:
            classification_dict["FP"].append(key)
        elif gt and not values["rm"]:
            classification_dict["FN"].append(key)
    # TP, FP, TN, FN = calculate_performance(data)
    TP = len(classification_dict["TP"])
    FP = len(classification_dict["FP"])
    TN = len(classification_dict["TN"])
    FN = len(classification_dict["FN"])

    # Calculate Accuracy, Precision, Recall, and F1 Score
    accuracy = (TP + TN) / (TP + FP + TN + FN)
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    f1_score = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    performance_metrics = {
        "True Positives": TP,
        "False Positives": FP,
        "True Negatives": TN,
        "False Negatives": FN,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1 Score": f1_score,
    }
    return performance_metrics, classification_dict

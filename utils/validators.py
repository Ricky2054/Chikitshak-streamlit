"""
Input validation utilities for medical workflow.
"""

ALLOWED_INPUT_TYPES = {"Symptoms", "Prescription Review", "Test Results"}


def validate_input(user_input, input_type):
    if input_type not in ALLOWED_INPUT_TYPES:
        return False
    if user_input is None:
        return False
    text = str(user_input).strip()
    if len(text) < 2:
        return False
    if len(text) > 8000:
        return False
    return True
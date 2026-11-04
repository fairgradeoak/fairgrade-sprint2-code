from typing import List, Dict
from pydantic import BaseModel, field_validator, model_validator
import json


class AiResponse(BaseModel):
    confidence: float
    student_feedback: str
    instructor_feedback: str
    criteria_count: int # Used to validate if all criteria are included
    rubric_breakdown: List[Dict]

    # Turns the raw text of a model reply into a validated AiResponse. Every way the reply can be wrong
    # (not json, not an object, a missing key, a wrong type) ends as a ValueError with a readable message,
    # so the caller can retry without caring which kind of mistake it was.
    @classmethod
    def from_model_reply(cls, reply_text, criteria_count):
        text = cls.strip_code_fences(reply_text)

        try:
            data = json.loads(text)
        except json.JSONDecodeError as error:
            raise ValueError(f"the reply is not valid json ({error})")

        if(not isinstance(data, dict)):
            raise ValueError(f"the reply should be a json object, received a {type(data).__name__}")

        required = ["confidence", "student_feedback", "instructor_feedback", "rubric_breakdown"]
        missing = [key for key in required if key not in data]
        if(missing):
            raise ValueError(f"the reply is missing the keys: {missing}")

        try:
            confidence = float(data["confidence"])
        except (TypeError, ValueError):
            raise ValueError(f"confidence should be a number, received a {type(data['confidence']).__name__}")

        return cls(confidence=confidence,
                   student_feedback=data["student_feedback"],
                   instructor_feedback=data["instructor_feedback"],
                   criteria_count=criteria_count,
                   rubric_breakdown=data["rubric_breakdown"])

    # models often wrap their json in ```json ... ``` even when told not to
    @staticmethod
    def strip_code_fences(text):
        text = text.strip()
        if(text.startswith("```")):
            text = text.split("\n", 1)[1] if "\n" in text else ""
            text = text.rsplit("```", 1)[0]
        return text.strip()

    @field_validator("confidence")
    def validate_confidence(confidence):
        if(confidence > 1 or confidence < 0 ):
            raise ValueError(f"confidence should be between 0 and 1, received value is: {confidence}")
        return confidence

    # Checks every criteria dictionary: it must have exactly the keys criteria_id and score, the id must look like c1, c2...
    # and the score must be a number between 0 and 1. Checking the keys first means a missing key
    # gives a clear message instead of a raw KeyError.
    @field_validator("rubric_breakdown")
    def validate_rubric_breakdown(rb):
        for position, criteria_dict in enumerate(rb, start=1):
            if(not isinstance(criteria_dict, dict)):
                raise ValueError(f"rubric_breakdown item {position} should be a dictionary, received a {type(criteria_dict).__name__}")

            for key in criteria_dict:
                if (key not in ["criteria_id","score"]):
                    raise ValueError(f"rubric_breakdown item {position} has a key other than criteria_id and score")

            for key in ["criteria_id","score"]:
                if(key not in criteria_dict):
                    raise ValueError(f"rubric_breakdown item {position} is missing the key '{key}'")

            id = criteria_dict["criteria_id"]
            if (not isinstance(id, str) or id[:1] != "c" or (not id[1:].isdigit())):
                raise ValueError(f"rubric_breakdown item {position} has an invalid criteria id")

            score = criteria_dict["score"]
            if(isinstance(score, bool) or not isinstance(score, (int, float))):
                raise ValueError(f"score of criteria {id} should be a number, received a {type(score).__name__}")
            if(score > 1 or score < 0):
                raise ValueError(f"criteria score should be between 0 and 1, received value: {score}")

        return rb

    @model_validator(mode="after")
    def validate_criteria_count(self):
        if(len(self.rubric_breakdown) != self.criteria_count):
            raise ValueError(f"Criteria amount mismatch. Question had {self.criteria_count}, ai gave {len(self.rubric_breakdown)}")
        return self

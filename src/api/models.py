from pydantic import BaseModel

from typing import List


class IngredientResponse(BaseModel):
    name: str
    grams: float
    kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float


class TotalsResponse(BaseModel):
    kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float


class AnalysisResult(BaseModel):
    ingredients: List[IngredientResponse]
    totals: TotalsResponse
    meal_recognized: bool

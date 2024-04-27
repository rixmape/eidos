from typing import List, Literal

from langchain_core.pydantic_v1 import BaseModel, Field


class RouteModel(BaseModel):
    """Response model for routing a message to either LLM or vectorstore."""

    explanation: str = Field(
        description="Explanation for the route.",
        default="",
    )
    decision: Literal["llm", "vectorstore"] = Field(
        description="Name of the route.",
        default="llm",
    )


class StatementQualityModel(BaseModel):
    """Model for the logical quality of a statement."""

    classification: Literal[
        "consistent",
        "inconsistent",
    ] = Field(
        description="Whether the statement is consistent or inconsistent.",
        default="consistent",
    )
    type: Literal[
        "fallacy",
        "external contradiction with philosophical texts",
        "external contradiction with previous statements",
        "internal contradiction within the statement",
        "unsupported claim",
    ] = Field(
        description="Type of inconsistency in the statement, if any.",
        default="",
    )
    explanation: str = Field(
        description="Explanation for the classification of the statement.",
        default="",
    )


class BeliefAdvicesModel(BaseModel):
    """Model for advicing ways to explore beliefs further."""

    advices: List[str] = Field(
        description="List of advices for exploring beliefs further.",
        default=[],
    )


class WebSearchQueriesModel(BaseModel):
    """Model for generating web search queries."""

    queries: List[str] = Field(
        description="List of web search queries.",
        default=[],
    )

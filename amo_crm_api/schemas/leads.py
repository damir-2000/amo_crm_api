from datetime import datetime
from typing import Annotated, List, Optional

from pydantic import AliasChoices, BaseModel, Field

from .base_model import BaseModelForFieldsSchema
from .common import CustomFieldsValueSchema


class LeadContactSchema(BaseModel):
    id: int
    is_main: bool


class LeadTagSchema(BaseModel):
    id: int
    name: str
    color: Optional[str] = None


class LeadEmbeddedSchema(BaseModel):
    tags: List[LeadTagSchema]
    companies: List
    contacts: List[LeadContactSchema]


class LeadSchema(BaseModelForFieldsSchema):
    id: Optional[int] = None
    name: Optional[str] = None
    price: Optional[int] = None
    responsible_user_id: Optional[int] = None
    group_id: Optional[int] = None
    status_id: Optional[int] = None
    old_status_id: Optional[int] = None
    pipeline_id: Optional[int] = None
    loss_reason_id: Optional[int] = None
    created_by: Annotated[
        Optional[int],
        Field(
            validation_alias=AliasChoices("created_by", "created_user_id"), exclude=True
        ),
    ] = None
    updated_by: Annotated[
        Optional[int],
        Field(
            validation_alias=AliasChoices("updated_by", "modified_user_id"),
            exclude=True,
        ),
    ] = None
    created_at: Annotated[
        Optional[datetime], Field(exclude=True)
    ] = None
    updated_at: Annotated[
        Optional[datetime], Field(exclude=True)
    ] = None
    closed_at: Annotated[
        Optional[datetime], Field(exclude=True)
    ] = None
    closest_task_at: Annotated[
        Optional[datetime], Field(exclude=True)
    ] = None
    is_deleted: Optional[bool] = None
    custom_fields_values: Annotated[
        Optional[List[CustomFieldsValueSchema]],
        Field(validation_alias=AliasChoices("custom_fields", "custom_fields_values")),
    ] = None
    score: Optional[float] = None
    account_id: Optional[int] = None
    labor_cost: Optional[float] = None
    embedded: Annotated[Optional[LeadEmbeddedSchema], Field(alias="_embedded")] = None
    contacts: Annotated[List[LeadContactSchema], Field(exclude=True)] = []

    def model_post_init(self, __context) -> None:
        if self.embedded and self.embedded.contacts:
            self.contacts = self.embedded.contacts
        super().model_post_init(__context)

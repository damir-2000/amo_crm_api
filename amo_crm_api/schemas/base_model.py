import inspect
from abc import ABC, abstractmethod
from datetime import date, datetime, time, timedelta, timezone
from functools import cached_property
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, field_serializer

from .common import CustomFieldsValueSchema, ValueSchema

t_zone = timezone(offset=timedelta(hours=5))


class CustomFieldType(ABC):
    valid_type: List[str] = []

    def __init__(
        self, field_id: Optional[int] = None, field_code: Optional[str] = None
    ) -> None:
        self.field_id = field_id
        self.field_code = field_code
        if (
            field_id
            and field_code
            or (field_id and not isinstance(field_id, int))
            or (field_code and not isinstance(field_code, str))
        ):
            raise ValueError

    @abstractmethod
    def on_get(self, values):
        raise NotImplementedError

    @abstractmethod
    def on_set(self, values):
        raise NotImplementedError


class TextField(CustomFieldType):
    """return -> str"""

    valid_type = ["text", "textarea"]

    def on_get(self, values: Optional[List[ValueSchema]]) -> Optional[str]:
        if values:
            return str(values[0].value)
        return None

    def on_set(self, values: str) -> CustomFieldsValueSchema:
        
        if values is None:
            values = ""
            
        return CustomFieldsValueSchema(
            field_id=self.field_id,
            field_code=self.field_code,
            values=[ValueSchema(value=values)],
        )


class URLField(TextField):
    valid_type = ["url"]


class AddressField(TextField):
    valid_type = ["streetaddress"]

class TrackingField(TextField):
    valid_type = ["tracking_data"]

class CheckboxField(CustomFieldType):
    """return -> bool"""

    valid_type = ["checkbox"]

    def on_get(self, values: Optional[List[ValueSchema]]) -> Optional[bool]:
        if values:
            return bool(values[0].value)
        return None

    def on_set(self, values: bool) -> CustomFieldsValueSchema:
        return CustomFieldsValueSchema(
            field_id=self.field_id,
            field_code=self.field_code,
            values=[ValueSchema(value=values)],
        )


class SelectField(CustomFieldType):
    """return -> Value"""

    valid_type = ["select", "multiselect"]

    def __init__(
        self,
        field_id: Optional[int] = None,
        field_code: Optional[str] = None,
        enums: Optional[Dict[Any, ValueSchema]] = None,
    ) -> None:
        self.enums = enums
        super().__init__(field_id, field_code)

    def on_get(
        self, values: Optional[List[ValueSchema]]
    ) -> Optional[Union[ValueSchema, Any]]:
        if values:
            value = values[0]

            if self.enums:
                for key, enum_value in self.enums.items():
                    if enum_value.enum_id == value.enum_id or (
                        not value.enum_id and enum_value.value == value.value
                    ):
                        return key

            return value
        return None

    def on_set(self, values: ValueSchema) -> Optional[CustomFieldsValueSchema]:
        assign_values = None
        if values is not None:
            if self.enums:
                if self.enums.get(values):
                    assign_values = [self.enums[values]]
                else:
                    raise ValueError(values)
            else:
                assign_values = [values]
        return CustomFieldsValueSchema(
            field_id=self.field_id, field_code=self.field_code, values=assign_values
        )


class RadioButtonField(SelectField):
    valid_type = ["radiobutton"]


class MultiSelectField(CustomFieldType):
    """return -> Value"""

    valid_type = ["multiselect"]

    def on_get(
        self, values: Optional[List[ValueSchema]]
    ) -> Optional[List[ValueSchema]]:
        if values:
            return values
        return None

    def on_set(self, values: List[ValueSchema]) -> CustomFieldsValueSchema:
        assign_values = None
        if values is not None:
            assign_values = values
        return CustomFieldsValueSchema(
            field_id=self.field_id, field_code=self.field_code, values=assign_values
        )


class MultiTextField(MultiSelectField):
    valid_type = ["multitext"]


class NumericField(CustomFieldType):
    """return -> Float"""

    valid_type = ["numeric"]

    def on_get(self, values: Optional[List[ValueSchema]]) -> Optional[float]:
        if values:
            value = values[0].value
            if isinstance(value, str):
                return float(value)
        return None

    def on_set(self, values: float) -> CustomFieldsValueSchema:
        assign_value = None
        if values is not None:
            assign_value = [ValueSchema(value=str(values))]
        return CustomFieldsValueSchema(
            field_id=self.field_id,
            field_code=self.field_code,
            values=assign_value,
        )


class DateField(CustomFieldType):
    """return -> Date"""

    valid_type = ["date", "date_time", "birthday"]

    def on_get(self, values: Optional[List[ValueSchema]]) -> Optional[date]:
        if values:
            value = values[0].value
            if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
                return datetime.fromtimestamp(int(value)).date()
            if isinstance(value, str):
                return datetime.strptime(value, "%d.%m.%Y").date()
        return None

    def on_set(self, values: date) -> CustomFieldsValueSchema:
        assign_value = None
        if values is not None:
            assign_value = [
                ValueSchema(
                    value=int(
                        datetime.combine(date=values, time=time(0, 0, 0, 0)).timestamp()
                    )
                )
            ]

        return CustomFieldsValueSchema(
            field_id=self.field_id, field_code=self.field_code, values=assign_value
        )


class DateTimeField(CustomFieldType):
    """return -> Datetime"""

    valid_type = ["date_time"]

    def on_get(self, values: Optional[List[ValueSchema]]) -> Optional[datetime]:
        if values:
            value = values[0].value
            if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
                return datetime.fromtimestamp(int(value))

        return None

    def on_set(self, values: datetime) -> CustomFieldsValueSchema:
        assign_value = None
        if values is not None:
            assign_value = [ValueSchema(value=int(values.timestamp()))]
        return CustomFieldsValueSchema(
            field_id=self.field_id,
            field_code=self.field_code,
            values=assign_value,
        )


class BaseModelForFieldsSchema(BaseModel):
    custom_fields_values: Optional[List[CustomFieldsValueSchema]] = None

    # @cached_property
    def _all_annotations(self) -> dict:
        all_annotations = {}
        for parent_cls in reversed(self.__class__.__mro__):
            all_annotations.update(inspect.get_annotations(parent_cls))
        return all_annotations

    # @cached_property
    def _custom_fields_type(self) -> dict:
        field_types = {}

        for key, field_type in self._all_annotations().items():
            if hasattr(field_type, "__metadata__"):
                for metadata in field_type.__metadata__:
                    if isinstance(metadata, CustomFieldType):
                        field_types[key] = metadata
                        continue

        return field_types

    def model_post_init(self, __context) -> None:
        if self.custom_fields_values and len(self.custom_fields_values) > 0:
            custom_fields: dict[Union[str, int], CustomFieldsValueSchema] = {}
            for custom_field in self.custom_fields_values:
                if custom_field.field_id:
                    custom_fields[custom_field.field_id] = custom_field
                if custom_field.field_code:
                    custom_fields[custom_field.field_code] = custom_field

            for key, custom_types in self._custom_fields_type().items():
                if custom_types.field_id:
                    field = custom_fields.get(custom_types.field_id)
                elif custom_types.field_code:
                    field = custom_fields.get(custom_types.field_code)

                if field:
                    if (
                        field.field_type
                        and field.field_type not in custom_types.valid_type
                    ):
                        raise TypeError
                    value = custom_types.on_get(values=field.values)
                    self.__setattr__(key, value)
    
    @field_serializer("custom_fields_values")
    def serialize_courses_in_order(
        self, custom_fields_values: Optional[List[CustomFieldsValueSchema]]
    ):
        if custom_fields_values is None:
            custom_fields_values = []

        new_custom_fields_values = []
        field_ids: List[Union[int, str]] = []

        for key, custom_types in self._custom_fields_type().items():
            values = self.__getattribute__(key)
            if custom_types.field_id is not None:
                field_ids.append(custom_types.field_id)
            if custom_types.field_code is not None:
                field_ids.append(custom_types.field_code)

            # if values is not None:
            field_with_value = custom_types.on_set(values=values)
            new_custom_fields_values.append(field_with_value)

        for custom_field in custom_fields_values:
            if (
                custom_field.field_id not in field_ids
                and custom_field.field_code not in field_ids
            ):
                new_custom_fields_values.append(custom_field)

        return new_custom_fields_values

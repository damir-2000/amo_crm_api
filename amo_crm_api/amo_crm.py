from functools import cached_property
from typing import Any, Dict, Generic, Iterable, List, Optional, Type, TypeVar, get_args

from pydantic import TypeAdapter

from .auth import BaseAuth
from .filters import Filter
from .schemas import (
    ComplexCreateResponseSchema,
    ContactSchema,
    CustomFieldSchema,
    LeadSchema,
    ListModelSchema,
    PipelineSchema,
    StatusSchema,
    UpdateResponseSchema,
    UserSchema,
    LinkSchema,
    LeadLossReasonSchema,
    TagSchema,
)

LeadType = TypeVar("LeadType", bound=LeadSchema)
ContactType = TypeVar("ContactType", bound=ContactSchema)


class AmoCRMApi(Generic[LeadType, ContactType]):
    def __init__(self, auth: BaseAuth) -> None:
        self._auth = auth
        self.request = self._auth.request
        super().__init__()

    def get_lead(self, lead_id: int) -> LeadType:
        response = self.request(
            method="GET",
            path=f"/leads/{lead_id}",
            params={"with": "contacts,loss_reason"},
        )
        return self._lead_model.model_validate_json(json_data=response.content)

    def get_lead_links(self, lead_id: int) -> List[LinkSchema]:
        response = self.request(
            method="GET",
            path=f"/leads/{lead_id}/links",
        )
        return (
            ListModelSchema[LinkSchema]
            .model_validate_json(response.content)
            .embedded.objects
        )

    def get_lead_list(
        self, filters: List[Filter] = [], limit: int = 50
    ) -> Iterable[LeadType]:
        model = self._lead_model
        params = {"with": "contacts,loss_reason", "limit": limit, "page": 1}
        params.update(self._filters_to_params(filters))
        return self._objects_list_generator(
            object_type=model, path="/leads", params=params
        )

    def create_lead(self, lead: LeadType) -> LeadType:
        response = self.request(
            method="POST", path="/leads", json=[lead.model_dump(exclude_unset=True)]
        )
        return response.content

    def create_complex_lead(
        self, lead: LeadType, contact: ContactType
    ) -> ComplexCreateResponseSchema:
        lead_data = lead.model_dump(exclude_unset=True)
        contact_data = contact.model_dump(exclude_unset=True)
        lead_data["_embedded"] = {}
        lead_data["_embedded"]["contacts"] = [contact_data]
        response = self.request(method="POST", path="/leads/complex", json=[lead_data])

        return TypeAdapter(List[ComplexCreateResponseSchema]).validate_json(
            response.content
        )[0]

    def update_lead(self, lead: LeadType) -> UpdateResponseSchema:
        lead_id = lead.id
        response = self.request(
            method="PATCH",
            path=f"/leads/{lead_id}",
            json=lead.model_dump(exclude_unset=True, by_alias=True),
        )
        return UpdateResponseSchema.model_validate_json(json_data=response.content)

    def get_contact(self, contact_id: int) -> ContactType:
        response = self.request(
            method="GET", path=f"/contacts/{contact_id}", params={"with": "leads"}
        )
        return self._contact_model.model_validate_json(json_data=response.content)

    def get_contact_links(self, contact_id: int) -> List[LinkSchema]:
        response = self.request(
            method="GET",
            path=f"/contacts/{contact_id}/links",
        )
        return (
            ListModelSchema[LinkSchema]
            .model_validate_json(response.content)
            .embedded.objects
        )

    def get_contact_list(
        self, filters: List[Filter] = [], limit: int = 50
    ) -> Iterable[ContactType]:
        model = self._contact_model
        params = {"with": "leads", "limit": limit, "page": 1}
        params.update(self._filters_to_params(filters))
        return self._objects_list_generator(
            object_type=model, path="/contacts", params=params
        )

    def create_contact(self, contact: ContactType) -> ContactType:
        response = self.request(
            method="POST",
            path="/contacts",
            json=[contact.model_dump(exclude_unset=True)],
        )
        return response.content

    def update_contact(self, contact: ContactType) -> UpdateResponseSchema:
        contact_id = contact.id
        response = self.request(
            method="PATCH",
            path=f"/contacts/{contact_id}",
            json=contact.model_dump(exclude_unset=True, by_alias=True),
        )
        return UpdateResponseSchema.model_validate_json(json_data=response.content)

    def get_pipeline(self, pipeline_id: int) -> PipelineSchema:
        response = self.request(method="GET", path=f"/leads/pipelines/{pipeline_id}")
        return PipelineSchema.model_validate_json(response.content)

    def get_pipeline_list(self) -> List[PipelineSchema]:
        response = self.request(method="GET", path="/leads/pipelines")
        return (
            ListModelSchema[PipelineSchema]
            .model_validate_json(json_data=response.content)
            .embedded.objects
        )

    def get_pipeline_status(self, pipeline_id: int, status_id: int) -> StatusSchema:
        response = self.request(
            method="GET", path=f"/leads/pipelines/{pipeline_id}/statuses/{status_id}"
        )
        return StatusSchema.model_validate_json(response.content)

    def get_pipeline_status_list(self, pipeline_id: int) -> List[StatusSchema]:
        response = self.request(
            method="GET", path=f"/leads/pipelines/{pipeline_id}/statuses"
        )
        return (
            ListModelSchema[StatusSchema]
            .model_validate_json(response.content)
            .embedded.objects
        )

    def get_custom_field(self, field_id: int) -> CustomFieldSchema:
        response = self.request(method="GET", path=f"/leads/custom_fields/{field_id}")
        return CustomFieldSchema.model_validate_json(response.content)

    def get_custom_field_list(self) -> Iterable[CustomFieldSchema]:
        # params = {"limit": 2, "page": 1}
        return self._objects_list_generator(
            object_type=CustomFieldSchema, path="/leads/custom_fields"
        )

    def get_user(self, user_id: int) -> UserSchema:
        response = self.request(method="GET", path=f"/users/{user_id}")
        return UserSchema.model_validate_json(response.content)

    def get_users(self) -> Iterable[UserSchema]:
        return self._objects_list_generator(object_type=UserSchema, path="/users")

    def get_loss_reason(self, loss_reason_id: int) -> LeadLossReasonSchema:
        response = self.request(
            method="GET", path=f"/leads/loss_reasons/{loss_reason_id}"
        )
        return LeadLossReasonSchema.model_validate_json(response.content)

    def get_loss_reason_list(self) -> List[LeadLossReasonSchema]:
        response = self.request(method="GET", path="/leads/loss_reasons")
        return (
            ListModelSchema[LeadLossReasonSchema]
            .model_validate_json(response.content)
            .embedded.objects
        )

    def get_lead_tags(self) -> Iterable[TagSchema]:
        return self._objects_list_generator(object_type=TagSchema, path="/leads/tags")

    @staticmethod
    def _filters_to_params(filters: List[Filter]) -> Dict[str, Any]:
        params = dict()
        for filter_obj in filters:
            params.update(filter_obj._as_params())
        return params

    @cached_property
    def _lead_model(self) -> type[LeadType]:
        args = get_args(self.__orig_class__)  # type: ignore
        base_type: type[LeadType] = LeadSchema  # type: ignore
        for arg in args:
            if issubclass(arg, base_type):
                return arg
        return base_type

    @cached_property
    def _contact_model(self) -> Type[ContactType]:
        args = get_args(self.__orig_class__)  # type: ignore
        base_type: Type[ContactType] = ContactSchema  # type: ignore
        for arg in args:
            if issubclass(arg, base_type):
                return arg
        return base_type

    def _objects_list_generator(
        self, object_type: type, path: str, params: Optional[dict] = None, limit=250
    ) -> Iterable[Any]:
        params = params if params else {}
        params["limit"] = params.get("limit", limit)
        params["page"] = params.get("page", 1)

        while True:
            response = self.request(method="GET", path=path, params=params)
            
            if response.status_code != 200:
                break
            item_list = (
                ListModelSchema[object_type]  # type: ignore
                .model_validate_json(response.content)
                .embedded.objects
            )

            for item in item_list:
                yield item

            params["page"] += 1

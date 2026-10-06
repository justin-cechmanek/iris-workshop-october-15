"""Lab 2 Context Retriever model. Complete the TODO fields before ctxctl."""

from context_surfaces.context_model import ContextField, ContextModel


class Store(ContextModel):
    __redis_key_template__ = "workshop:store:{store_id}"

    store_id: str = ContextField(description="Demo store ID", is_key_component=True)
    name: str = ContextField(description="Demo store name", index="text")
    # TODO: model city as text and pickup_status as a tag.


class Order(ContextModel):
    __redis_key_template__ = "workshop:order:{order_id}"

    order_id: str = ContextField(description="Demo retail order ID", is_key_component=True)
    # TODO: model store_id, status, and customer_id as tags.
    # TODO: model item_summary as text.

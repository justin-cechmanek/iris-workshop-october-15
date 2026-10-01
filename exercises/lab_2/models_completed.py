"""Completed lab 2 model: Redis HASH fields exposed as Context Retriever tools.

Use this file with ctxctl --models exercises/lab_2/models_completed.py when trying
the completed scripts. Key templates must match 02_load_context_completed.py.
"""

from context_surfaces.context_model import ContextField, ContextModel


class Store(ContextModel):
    __redis_key_template__ = "workshop:store:{store_id}"

    # A key component identifies one HASH; text fields support word search,
    # while tag fields support exact filtering.
    store_id: str = ContextField(description="Demo store ID", is_key_component=True)
    name: str = ContextField(description="Demo store name", index="text")
    city: str = ContextField(description="Store city", index="text")
    pickup_status: str = ContextField(description="Whether pickup is open", index="tag")


class Order(ContextModel):
    __redis_key_template__ = "workshop:order:{order_id}"

    order_id: str = ContextField(description="Demo retail order ID", is_key_component=True)
    store_id: str = ContextField(description="Store fulfilling this order", index="tag")
    status: str = ContextField(description="Current order status", index="tag")
    item_summary: str = ContextField(description="Retail items in the order", index="text")
    customer_id: str = ContextField(description="Fictional customer ID", index="tag")

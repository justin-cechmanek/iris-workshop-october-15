"""Completed lab 2: inspect generated tools, then fetch one live order.

First create a Context Retriever surface with models_completed.py and put
CTX_AGENT_KEY in .env. Run: python exercises/lab_2/02_context_completed.py
"""

import asyncio
import json
import os

from context_surfaces import UnifiedClient
from dotenv import load_dotenv


async def main():
    load_dotenv()
    agent_key = os.environ["CTX_AGENT_KEY"]

    async with UnifiedClient() as client:
        # The surface generated these tools from models_completed.py. Print
        # every complete definition, including fields beyond inputSchema.
        tools = await client.list_tools(agent_key)
        tool_details = [
            tool if isinstance(tool, dict) else tool.model_dump(by_alias=True)
            for tool in tools
        ]
        print(f"Generated tools ({len(tool_details)}):")
        for details in tool_details:
            print(json.dumps(details, indent=2))

        tool_name = "get_order_by_id"
        names = {details["name"] for details in tool_details}
        if tool_name not in names:
            raise RuntimeError(f"{tool_name} was not generated; check the surface model")

        # A primary key produces get_<entity>_by_id with an 'id' argument.
        # This call uses the agent key, not the admin key or a raw Redis query.
        result = await client.query_tool(
            agent_key=agent_key, tool_name=tool_name, arguments={"id": "O1001"}
        )
        if result.get("isError"):
            raise RuntimeError(result)
        content = result["content"][0]
        order = json.loads(content["text"])
        print("Order O1001:")
        print(json.dumps(order, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

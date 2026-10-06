"""Lab 2: inspect and call a generated Context Retriever tool.

Run from repository root: python exercises/lab_2/02_context.py
"""

import asyncio
import os

from context_surfaces import UnifiedClient
from dotenv import load_dotenv


async def main():
    load_dotenv()
    async with UnifiedClient() as client:
        # TODO 1: list_tools(os.environ["CTX_AGENT_KEY"]) and print every
        # full tool definition. A tool may be a dict or an SDK model (use
        # model_dump(by_alias=True) in that case).
        # TODO 2: choose the generated get-by-ID tool for Order. Copy its
        # exact name and argument schema from the printed list.
        # TODO 3: query_tool(agent_key=..., tool_name=..., arguments=...)
        # for O1001. Print the returned object.
        raise NotImplementedError("List and call a generated tool")


if __name__ == "__main__":
    asyncio.run(main())

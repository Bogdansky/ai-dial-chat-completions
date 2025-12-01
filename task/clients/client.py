from aidial_client import Dial, AsyncDial

from task.clients.base import BaseClient
from task.constants import DIAL_ENDPOINT, API_KEY
from task.models.message import Message
from task.models.role import Role


class DialClient(BaseClient):

    def __init__(self, deployment_name: str):
        super().__init__(deployment_name)
        # TODO:
        # Documentation: https://pypi.org/project/aidial-client/ (here you can find how to create and use these clients)
        # 1. Create Dial client
        self._client = Dial(api_key=API_KEY, base_url=DIAL_ENDPOINT)
        # 2. Create AsyncDial client
        self._async_client = AsyncDial(api_key=API_KEY, base_url=DIAL_ENDPOINT)

    def get_completion(self, messages: list[Message]) -> Message:
        # TODO:
        # 1. Create chat completions with client
        #    Hint: to unpack messages you can use the `to_dict()` method from Message object
        message_dicts = [msg.to_dict() for msg in messages]
        response = self._client.chat.completions.create(
            deployment_name=self._deployment_name,
            messages=message_dicts
        )
        
        # 2. Get content from response, print it and return message with assistant role and content
        # 3. If choices are not present then raise Exception("No choices in response found")
        if not response.choices:
            raise Exception("No choices in response found")
        
        content = response.choices[0].message.content
        print(f"Assistant: {content}")
        
        return Message(role=Role.AI, content=content)

    async def stream_completion(self, messages: list[Message]) -> Message:
        # TODO:
        # 1. Create chat completions with async client
        #    Hint: don't forget to add `stream=True` in call.
        message_dicts = [msg.to_dict() for msg in messages]
        chunks = await self._async_client.chat.completions.create(
            deployment_name=self._deployment_name,
            messages=message_dicts,
            stream=True
        )
        
        # 2. Create array with `contents` name (here we will collect all content chunks)
        contents = []
        
        # 3. Make async loop from `chunks` (from 1st step)
        # 4. Print content chunk and collect it contents array
        print("Assistant: ", end="", flush=True)
        async for chunk in chunks:
            if chunk.choices and chunk.choices[0].delta.content:
                content_part = chunk.choices[0].delta.content
                print(content_part, end="", flush=True)
                contents.append(content_part)
        
        # 5. Print empty row `print()` (it will represent the end of streaming and in console we will print input from a new line)
        print()
        
        # 6. Return Message with assistant role and message collected content
        full_content = "".join(contents)
        return Message(role=Role.AI, content=full_content)

import json
import aiohttp
import requests

from task.clients.base import BaseClient
from task.constants import DIAL_ENDPOINT, API_KEY
from task.models.message import Message
from task.models.role import Role


class CustomDialClient(BaseClient):
    _endpoint: str
    _api_key: str

    def __init__(self, deployment_name: str):
        super().__init__(deployment_name)
        self._endpoint = DIAL_ENDPOINT + f"/openai/deployments/{deployment_name}/chat/completions"
        self._api_key = API_KEY

    def get_completion(self, messages: list[Message]) -> Message:
        # TODO:
        # Take a look at README.md of how the request and regular response are looks like!
        # 1. Create headers dict with api-key and Content-Type
        headers = {
            "Api-Key": self._api_key,
            "Content-Type": "application/json"
        }
        
        # 2. Create request_data dictionary with:
        #   - "messages": convert messages list to dict format using msg.to_dict() for each message
        request_data = {
            "model": self._deployment_name,
            "messages": [msg.to_dict() for msg in messages]
        }
        
        # Print request for debugging
        print(f"\n[CustomDialClient] Request:")
        print(f"  URL: {self._endpoint}")
        print(f"  Headers: {headers}")
        print(f"  Data: {json.dumps(request_data, indent=2)}")
        
        # 3. Make POST request using requests.post() with:
        #   - URL: self._endpoint
        #   - headers: headers from step 1
        #   - json: request_data from step 2
        response = requests.post(
            self._endpoint,
            headers=headers,
            json=request_data
        )
        
        # 5. If status code != 200 then raise Exception with format: f"HTTP {response.status_code}: {response.text}"
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        
        # Print response for debugging
        print(f"[CustomDialClient] Response: {response.text}\n")
        
        response_json = response.json()
        
        # 4. Get content from response, print it and return message with assistant role and content
        if "choices" not in response_json or not response_json["choices"]:
            raise Exception("No choices in response found")
        
        content = response_json["choices"][0]["message"]["content"]
        print(f"Assistant: {content}")
        
        return Message(role=Role.AI, content=content)

    async def stream_completion(self, messages: list[Message]) -> Message:
        # TODO:
        # Take a look at README.md of how the request and streamed response chunks are looks like!
        # 1. Create headers dict with api-key and Content-Type
        headers = {
            "Api-Key": self._api_key,
            "Content-Type": "application/json"
        }
        
        # 2. Create request_data dictionary with:
        #    - "stream": True  (enable streaming)
        #    - "messages": convert messages list to dict format using msg.to_dict() for each message
        request_data = {
            "model": self._deployment_name,
            "stream": True,
            "messages": [msg.to_dict() for msg in messages]
        }
        
        # Print request for debugging
        print(f"\n[CustomDialClient] Streaming Request:")
        print(f"  URL: {self._endpoint}")
        print(f"  Headers: {headers}")
        print(f"  Data: {json.dumps(request_data, indent=2)}\n")
        
        # 3. Create empty list called 'contents' to store content snippets
        contents = []
        # track whether we've already warned about content filter errors to avoid noise
        _content_filter_warned = False
        
        # 4. Create aiohttp.ClientSession() using 'async with' context manager
        async with aiohttp.ClientSession() as session:
            # 5. Inside session, make POST request using session.post() with:
            #    - URL: self._endpoint
            #    - json: request_data from step 2
            #    - headers: headers from step 1
            #    - Use 'async with' context manager for response
            async with session.post(
                self._endpoint,
                json=request_data,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
                
                # 6. Get content from chunks (don't forget that chunk start with `data: `, final chunk is `data: [DONE]`), print
                #    chunks, collect them and return as assistant message
                print("Assistant: ", end="", flush=True)
                async for line in response.content:
                    if not line:
                        continue
                    line_str = line.decode('utf-8').strip()
                    if not line_str.startswith("data: "):
                        continue
                    chunk_str = line_str[6:]  # Remove "data: " prefix

                    if chunk_str == "[DONE]":
                        break

                    try:
                        chunk_json = json.loads(chunk_str)
                    except json.JSONDecodeError:
                        continue

                    # Check for content filter errors and warn once
                    try:
                        cfr = chunk_json.get("choices", [])[0].get("content_filter_result")
                        if cfr and isinstance(cfr, dict) and cfr.get("error") and not _content_filter_warned:
                            err_msg = cfr.get("error", {}).get("message") or str(cfr.get("error"))
                            print(f"[CustomDialClient] Warning: content_filter_result error: {err_msg}", file=__import__('sys').stderr)
                            _content_filter_warned = True
                    except Exception:
                        # ignore unexpected structure
                        pass

                    # Extract content delta if present
                    choices = chunk_json.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    content_part = delta.get("content")
                    if content_part:
                        print(content_part, end="", flush=True)
                        contents.append(content_part)
        
        print()
        full_content = "".join(contents)
        return Message(role=Role.AI, content=full_content)


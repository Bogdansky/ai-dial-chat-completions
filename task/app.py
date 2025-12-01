import asyncio

from task.clients.client import DialClient
from task.clients.custom_client import CustomDialClient
from task.constants import DEFAULT_SYSTEM_PROMPT
from task.models.conversation import Conversation
from task.models.message import Message
from task.models.role import Role


async def start(stream: bool, deployment_name: str) -> None:
    # 1.1. Create DialClient using provided deployment_name
    # (you can get available deployment_name via https://ai-proxy.lab.epam.com/openai/models
    #  you can import Postman collection to make a request, file in the project root `dial-basics.postman_collection.json`
    #  don't forget to add your API_KEY)
    dial_client = DialClient(deployment_name)
    
    # 1.2. Create CustomDialClient
    custom_client = CustomDialClient(deployment_name)
    
    # 2. Create Conversation object
    conversation = Conversation()
    
    # 3. Get System prompt from console or use default -> constants.DEFAULT_SYSTEM_PROMPT and add to conversation messages.
    system_prompt = input("Enter system prompt (press Enter to use default): ").strip()
    if not system_prompt:
        system_prompt = DEFAULT_SYSTEM_PROMPT
    
    system_message = Message(role=Role.SYSTEM, content=system_prompt)
    conversation.add_message(system_message)
    
    # Select which client to use
    client = custom_client if stream else dial_client
    print(f"\nUsing {'CustomDialClient' if stream else 'DialClient'} with stream={stream}")
    print(f"System prompt: {system_prompt}\n")
    
    # 4. Use infinite cycle (while True) and get user message from console
    while True:
        user_input = input("You: ").strip()
        
        # 5. If user message is `exit` then stop the loop
        if user_input.lower() == "exit":
            print("Exiting conversation...")
            break
        
        if not user_input:
            continue
        
        # 6. Add user message to conversation history (role 'user')
        user_message = Message(role=Role.USER, content=user_input)
        conversation.add_message(user_message)
        
        # 7. If `stream` param is true -> call DialClient#stream_completion()
        #    else -> call DialClient#get_completion()
        try:
            if stream:
                assistant_message = await custom_client.stream_completion(conversation.get_messages())
            else:
                assistant_message = dial_client.get_completion(conversation.get_messages())
            
            # 8. Add generated message to history
            conversation.add_message(assistant_message)
            print()
        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run DIAL chat client")
    parser.add_argument("-d", "--deployment-name", default="gpt-4o", help="Deployment name to use (default: gpt-4o)")
    parser.add_argument("--stream", action="store_true", help="Use streaming CustomDialClient (default: False)")
    args = parser.parse_args()

    asyncio.run(start(args.stream, args.deployment_name))

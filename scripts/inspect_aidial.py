from aidial_client import Dial
import inspect
import os

# Use environment API key if available (script run inside project venv where DIAL_API_KEY is set)
api_key = os.environ.get('DIAL_API_KEY')
c = Dial(api_key=api_key, base_url='https://ai-proxy.lab.epam.com')
fn = c.chat.completions.create
print('signature:', inspect.signature(fn))
print('\nDoc:')
print((fn.__doc__ or '')[:1200])

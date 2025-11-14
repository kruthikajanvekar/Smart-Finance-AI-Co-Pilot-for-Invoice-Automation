import os
from config import Config
import google.generativeai as genai

genai.configure(api_key=Config.GOOGLE_API_KEY)

model = genai.GenerativeModel(Config.GEMINI_MODEL)

prompt = "Write a short professional invoice follow-up email (under 100 words)."

resp = model.generate_content([prompt], generation_config={"temperature":0.7, "max_output_tokens":300})

print('TYPE:', type(resp))
print('DIR resp:', dir(resp))

# try result
res = getattr(resp, 'result', None)
print('\nresult attr type:', type(res))
print('DIR result:', dir(res) if res is not None else None)

# inspect candidates
try:
    candidates = getattr(res, 'candidates', None)
    print('\ncandidates:', candidates)
    if candidates:
        print('\nfirst candidate type:', type(candidates[0]))
        first = candidates[0]
        print('DIR first candidate:', dir(first))
        content = getattr(first, 'content', None)
        print('content attr type:', type(content))
        print('DIR content:', dir(content) if content is not None else None)
        if content is not None:
            # try parts
            parts = getattr(content, 'parts', None)
            print('content.parts:', parts)
            # try converting proto to dict
            try:
                from google.protobuf.json_format import MessageToDict
                pb = getattr(resp, '_pb', None) or res
                if pb is not None:
                    d = MessageToDict(pb)
                    print('\nMessageToDict result keys:', list(d.keys()))
                    import json
                    print('\nMessageToDict dump (candidates):')
                    print(json.dumps(d.get('candidates', d), indent=2)[:2000])
            except Exception as e:
                print('MessageToDict failed:', e)
except Exception as e:
    print('Error inspecting response:', e)

print('\nFULL REPR:')
print(repr(resp))

import google.generativeai as genai
genai.configure(api_key="AIzaSyDEZm4q6AEKKMmER8Xc6FIuCrgepIGJv1k")

model = genai.GenerativeModel('models/gemini-pro-latest')
res = model.generate_content("Write a 1-line greeting")
print(res.text)
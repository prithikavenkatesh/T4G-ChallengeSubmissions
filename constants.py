from google import genai

MODEL = "gemini-3.1-pro-preview"
JUDGE_MODEL = "gemini-3.1-pro-preview"
REQUIRED_FRONTMATTER_FIELDS = ["name", "description"]

client = genai.Client()

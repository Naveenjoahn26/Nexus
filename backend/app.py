import os
import gradio as gr

# Pre-download ML models before starting the server so the first request doesn't timeout!
print("Pre-downloading ML models for Hugging Face Space...")
try:
    from sentence_transformers import SentenceTransformer, CrossEncoder
    SentenceTransformer('BAAI/bge-small-en-v1.5')
    CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    print("Models ready!")
except Exception as e:
    print(f"Failed to pre-download models: {e}")

# Import your actual FastAPI application
from app.main import app as fastapi_app

# Create a dummy Gradio interface (Hugging Face requires a Gradio UI to be present)
def status_check():
    return "✅ NEXUS EDU Backend is running securely in the background!"

demo = gr.Interface(
    fn=status_check, 
    inputs=None, 
    outputs="text", 
    title="NEXUS EDU Backend Status"
)

# This is the magic! We mount the Gradio UI at "/gradio"
# This leaves your entire FastAPI app running at the root ("/") exactly like before!
# All your /api/v1/... routes will work perfectly.
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

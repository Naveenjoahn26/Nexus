import os
import gradio as gr

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

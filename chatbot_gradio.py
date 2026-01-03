import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv
from pypdf import PdfReader
import base64
import os

load_dotenv()

openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def image_to_base64(image_file):
    with open(image_file.name, "rb") as img:
        return base64.b64encode(img.read()).decode("utf-8")

def read_file(file):
    if file is None:
        return ""
    if file.name.endswith(".pdf"):
        reader = PdfReader(file.name)
        return "\n".join(page.extract_text() for page in reader.pages)
    if file.name.endswith(".txt"):
        with open(file.name, "r", encoding="utf-8") as f:
            return f.read()
    return ""

system_prompt = """
You are an assistant who can analyze uploaded images and files,
giving short, clear, and natural answers.

Rules:
- Perform OCR if there are images, interpret if it's a graphic, analyze if it's a product
- Don't specifically mention that you are reading or analyzing files
- Use the chat context but don't make it obvious
"""

def chat(message, file, history):
    history = history or []

    messages = [{"role": "system", "content": system_prompt}]

    for msg in history:
        messages.append(msg)

    if file and file.name.lower().endswith((".png", ".jpg", ".jpeg")):
        img_base64 = image_to_base64(file)
        user_message = {
            "role": "user",
            "content": [
                {"type": "text", "text": message},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_base64}"
                    }
                }
            ]
        }
    elif file and file.name.lower().endswith((".pdf", ".txt")):
        file_text = read_file(file)[:8000]
        user_message = {
            "role": "user",
            "content": f"Aşağıdaki dosyayı bağlam olarak kullan:\n{file_text}\n\nSoru: {message}"
        }
    else:
        user_message = {"role": "user", "content": message}

    messages.append(user_message)

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7
    )

    answer = response.choices[0].message.content

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": answer})

    return history, history, ""


with gr.Blocks() as demo:
    gr.Markdown("# 📂 Dosya Analiz Chatbotu")

    state = gr.State([])

    chatbot = gr.Chatbot(height=450)

    with gr.Row(equal_height=True):
        msg = gr.Textbox(placeholder="Mesajını yaz...", show_label=False, scale=7)
        file = gr.File(file_types=[".png", ".jpg", ".jpeg", ".pdf", ".txt"], show_label=False, scale=1)
        send = gr.Button("Gönder", scale=1)

    gr.Examples(
        examples=[
            "Bu görselde ne yazıyor?",
            "Bu grafikten hangi sonuçları çıkarabiliriz?",
            "Bu ürün fotoğrafına göre satış açıklaması yaz",
            "Bu dosyayı özetler misin?",
            "Bu metindeki hataları bul"
        ],
        inputs=msg
    )

    send.click(chat, inputs=[msg, file, state], outputs=[chatbot, state])
    msg.submit(chat, inputs=[msg, file, state], outputs=[chatbot, state])

demo.launch()
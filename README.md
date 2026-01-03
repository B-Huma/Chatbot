git clone https://github.com/username/repo-name.git
cd repo-name

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# .env içine API key yaz

python chatbot_gradio.py

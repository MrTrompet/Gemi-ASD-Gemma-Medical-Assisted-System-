🩺❤️Gemi-ASD: Gemma-Powered Medical Assistant System

Gemi is an on-device medical assistant leveraging the power of Gemma 3n to provide crucial diagnoses and emergency guidance to millions, especially in low-resource settings without internet access.

🌟 Project Vision

Our goal is to democratize access to critical health information. Gemi operates entirely on-device, ensuring that life-saving advice and medical assistance are available instantly, regardless of internet connectivity.

✨ Key Features

- Emergency Flow: A life-saving feature that provides immediate, actionable guidance in critical situations, such as a Red Alert for a high risk of CVA (stroke). It guides the user through a rapid diagnostic process and provides concise instructions.

- Pulsometer (15s Method): An innovative, sensorless tool that allows users to accurately check their pulse and heart rate. It provides a BPM count and a preliminary diagnosis (tachycardia, bradycardia) using a quick, 15-second manual count method, inspired by emergency room protocols.

- Medication Calendar: Simplifies medication management by allowing users to schedule reminders. The system can understand natural language input and generate a clear, manageable schedule to ensure patients adhere to their treatment.

- Medical Records Viewer: 
A built-in PDF viewer designed for easy access and review of personal medical records, ensuring all critical information is available in one place.

🛠️ Technical Stack

- LLM: Gemma-3n-E2B-it-Q4_K_M.gguf - Unsloth

- Quantization: 4-bit (.gguf) using llama.cpp for optimal on-device performance.

- Framework: Python for the backend, with Flet for a multi-platform, cross-device graphical user interface (GUI).

🚀 Demo and Installation

- YouTube Demo: Watch the full demonstration of Gemi's features and functionality here:
  ▶️ https://www.youtube.com/watch?v=1Ofr-tD4PQw

- Executable (.exe): To test the application directly, download the compiled executable from our Google Drive.
  📂 https://drive.google.com/file/d/1pfiUnHVRXyYFDlg6kSTK3TaSBGV6DwrX/view?usp=sharing

💻 For Developers

Setup & Run from Source

To run the application from the source code, follow these steps:

Clone the Repository

Bash

git clone https://github.com/MrTrompet/Gemi-ASD-Gemma-Medical-Assisted-System-
cd Gemi-ASD-Gemma-Medical-Assisted-System-
Set up the Environment
Create a Python virtual environment and install the required dependencies.

Bash

# Create the virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
Download the Gemma 3n Model
The application requires the Gemma 3n 4-bit quantized model (.gguf). This file is not included in the repository due to its size.

Download the model: The model was generated using the Unsloth library. You can download the .gguf file from the following link: https://huggingface.co/bartowski/google_gemma-3n-E2B-it-GGUF

Place the Model
Create a new folder and place the downloaded model file in it.

./gemi_app
├── models-gemma3n/
│   └── gemma-3n-E2B-it-Q4_K_M.gguf
└── ...

🔧Project Structure: 

gemi_app/
├─ app.py  # punto de entrada: carga el page, routes y llama a ft.app()
├─ utils.py 
├─ text_utils.py 
├─ _init_.py
├─ requirements.txt
├─ .venv
├─ > assets
│    └─ Guarda el cache de Pdfs
├─ llm/
│   ├─ __init__.py
│   ├─ prompt_builder.py
│   └─ gemma_wrapper.py 
├─ views/
│   ├─ logo.py      # build_logo_view()
│   ├─ privacy.py   # build_privacy_view()
│   ├─ onboarding.py# build_gender_view(), build_age_view(), build_antecedents_view()
│   ├─ main.py      # build_main_view(), set_tab(), toggle_drawer()
│   ├─ emergency.py # build_emergency_tab()
│   ├─ medichat.py  # build_medichat_tab()
│   ├─ profile.py   # build_profile_view()
│   ├─ pdf_viewer_proc.py
│   ├─ pdf_image_viewer.py
│   ├─ pdf_text_viewer.py
│   ├─ _init_.py
│   ├─ calendario.py
│   ├─ pulsometro.py
│   ├─ emergency_button.py
│   └─ settings.py  # build_settings_view()
└─ models\gemma3n
│    ├─ gemma-3n-2b-it-gguf
│         ├─ >.cache
│         │     ├─ >download
│         │     │     └─ gemma-3n-E2B-it-Q4_K_M.gguf.metadata
│         │     └─ .gitignore
│         └─ gemma-3n-E2B-it-Q4_K_M.gguf            
└─ data/
│     ├─ > pdfs
│     ├─ > photos
│     ├─ chat_data.json
│     ├─ profile_data.json
│     └─ gemi_user_data.json


Run the Application
With the virtual environment active and the model in place, you can run the application.

Bash

python app.py

⚙️ Challenges and Lessons Learned
This project was a journey of technical problem-solving. A major challenge was optimizing the model for low-end hardware.

The Quantization Pivot: I initially attempted to quantize the model to 8-bit using ONNX Runtime. However, this method proved to be too heavy for the target hardware. As a result, I decided to pivot to a more effective method, successfully using llama.cpp to achieve a highly efficient 4-bit (.gguf) model that runs flawlessly on a standard CPU.

Experimentation Notebook: For full transparency, the notebook detailing the attempted 8-bit ONNX quantization is available in this repository.

🤝 Connect and Contribute
I am very interested in receiving your feedback to continue improving and developing this application in the future. Feel free to contact me or open an issue on this repository.

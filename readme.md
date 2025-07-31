# 📞 Rick Roll Call Backend

> An AI-powered answering machine API that combines Google Gemini AI, text-to-speech, and Twilio phone services to create interactive voice experiences!

## 🎯 What This Does

This FastAPI backend provides:

- 🤖 **AI-powered responses** using Google Gemini
- 🔊 **Text-to-speech conversion** via Google Cloud
- 📱 **Phone call automation** through Twilio
- ☁️ **File storage** with Google Cloud Storage
- 🎵 **Audio streaming** capabilities
- 🌐 **RESTful API** for frontend integration

## 🚀 Quick Start

### Prerequisites

🐍 **Python 3.9+** is required

### 📦 Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/coreyloftus/rick-roll-call-backend.git
   cd rick-roll-call-backend
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (see [Environment Setup](#-environment-setup) below)

5. **Run the application**

   ```bash
   # Option 1: Using the start script
   chmod +x start.sh
   ./start.sh

   # Option 2: Direct uvicorn command
   uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload

   # Option 3: FastAPI dev server
   fastapi dev src/main.py
   ```

## 🔧 Environment Setup

Create a `.env` file in the root directory with the following variables:

```env
# 🤖 Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# ☁️ Google Cloud Services
SERVICE_ACCOUNT_KEY_JSON={"type":"service_account","project_id":"..."}
GCS_STORAGE_BUCKET=your_bucket_name

# 📱 Twilio Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# 🚀 Application Settings
PORT=8080
```

### 🔑 Getting API Keys

1. **Google Gemini API Key**

   - Visit [Google AI Studio](https://aistudio.google.com/)
   - Create a new API key
   - Add it to your `.env` file

2. **Google Cloud Service Account**

   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a service account with Text-to-Speech and Storage permissions
   - Download the JSON key and add it to your `.env` file

3. **Twilio Credentials**
   - Sign up at [Twilio](https://www.twilio.com/)
   - Get your Account SID, Auth Token, and phone number
   - Add them to your `.env` file

## 🐳 Docker Setup

**Build and run with Docker:**

```bash
# Build the image
docker build -t rick-roll-call-backend .

# Run the container
docker run -p 8080:8080 --env-file .env rick-roll-call-backend
```

## 📋 API Endpoints

### 🏠 Health Check

- `GET /` - Basic health check
- `GET /health` - Detailed health status
- `GET /test` - Simple test endpoint

### 🤖 AI & Text Processing

- `POST /gemini` - Generate AI text responses
- `POST /gemini/audio` - Generate audio responses
- `POST /gemini/stream` - Stream AI responses
- `POST /sanity_check` - Validate prompts
- `POST /flowcode_demo` - Demo endpoint

### 📁 File Management

- `POST /gcs/upload` - Upload files to Google Cloud Storage

### 📞 Phone Services

- `POST /twilio/call` - Make phone calls with custom audio

### 📖 API Documentation

Once running, visit:

- 📚 **Swagger UI**: `http://localhost:8080/docs`
- 📋 **ReDoc**: `http://localhost:8080/redoc`

## 🧪 Testing

Test the API with curl:

```bash
# Health check
curl http://localhost:8080/health

# AI text generation
curl -X POST "http://localhost:8080/gemini" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, AI!"}'
```

## 🚨 Troubleshooting

### Common Issues

🔴 **ImportError: Missing dependencies**

```bash
pip install -r requirements.txt
```

🟡 **Environment variables not loaded**

- Ensure your `.env` file is in the root directory
- Check that all required variables are set

🟠 **Google Cloud authentication issues**

- Verify your service account JSON is valid
- Ensure proper permissions are set

🔵 **Twilio connection problems**

- Check your account SID and auth token
- Verify your phone number is valid

## 🎯 Development

### 🔄 Development Mode

```
`fastapi dev main.py`
```

## 🌟 Features

✨ **AI-Powered**: Leverages Google Gemini for intelligent responses
🎙️ **Voice Synthesis**: Convert text to natural-sounding speech
📲 **Phone Integration**: Make automated calls with custom messages
🌐 **CORS Enabled**: Ready for frontend integration
🔒 **Secure**: Environment-based configuration
📱 **Mobile Ready**: Responsive API design
🚀 **Cloud Ready**: Docker support for easy deployment

## 📧 Contact & Support

**👨‍💻 Developer**: Corey Loftus

Feel free to reach out for questions, suggestions, or collaborations!

- 🐙 **GitHub**: [@coreyloftus](https://github.com/coreyloftus)
- 📧 **Email**: [your-email@example.com](mailto:your-email@example.com)
- 💼 **LinkedIn**: [linkedin.com/in/coreyloftus](https://linkedin.com/in/coreyloftus)

## 📄 License

This project is open source. Feel free to use and modify as needed!

---

⭐ **Star this repo** if you found it helpful!

🚀 **Happy coding!**

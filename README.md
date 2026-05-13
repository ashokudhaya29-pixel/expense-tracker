An AI-powered Expense Tracker that allows users to send voice/text messages through WhatsApp to track expenses automatically using Generative AI
Features:
		- WhatsApp-based expense tracking
		- Voice-to-text transcription using Whisper
		- AI-powered expense extraction
		- Expense categorization using LLM
		- Monthly expense dashboard
		- Daily summary reports
		- Supabase database integration
		- FastAPI backend APIs
		- Streamlit analytics dashboard	
Architecture:
			WhatsApp User
			↓
			Twilio Webhook
			↓
			FastAPI Backend
			↓
			Whisper Transcription
			↓
			LLM Expense Extraction
			↓
			Supabase Database
			↓
			Streamlit Dashboard
Tech Stack:
			- Python
			- FastAPI
			- Streamlit
			- Whisper
			- Supabase
			- Twilio
			- Generative AI
			- REST APIs
Installation Steps:
			```bash
			git clone https://github.com/your-repo.git
			cd expense-tracker
			pip install -r requirements.txt
			uvicorn main:app --reload
Environment Variables:
			```md
			## Environment Variables
			
			Create a `.env` file and add:
			
			```env
			SUPABASE_URL=your_url
			SUPABASE_KEY=your_key
			TWILIO_AUTH_TOKEN=your_token	
API Endpoints:
			```md
			## API Endpoints
			
			- POST /whatsapp
			- GET /ping
			- GET /send-daily-summary
Future Enhancements
			- Multi-user authentication
			- AI spending insights
			- Budget prediction
			- AI financial assistant
			- Multi-agent workflows
			

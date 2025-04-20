# Daily Digest - Calendar Gmail Summary

A full-stack application that provides smart summaries of your calendar events and Gmail messages using Google's Gemini AI. The application includes text and audio summaries, smart replies, and priority-based organization of your daily schedule.

## Features

- OAuth2 authentication with Google Calendar and Gmail
- AI-powered daily summaries of calendar events and emails
- Text-to-Speech summaries
- Priority-based organization of events and emails
- Smart reply suggestions for emails
- Real-time calendar invite management
- Secure SSL/TLS communication
- MongoDB database integration

## Prerequisites

- Python 3.8+
- Node.js 16+
- MongoDB
- Google Cloud Platform account with Calendar and Gmail APIs enabled
- Gemini API key

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Calendar-Gmail-Summary.git
cd Calendar-Gmail-Summary
```

### 2. Backend Setup

1. Create and activate a Python virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
Create a `.env` file in the backend directory with the following variables:
```
FLASK_SECRET_KEY=your_secret_key
FRONTEND_URL=https://localhost:3001
MONGO_URI=mongodb://127.0.0.1:27017/
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GEMINI_API_KEY=your_gemini_api_key
```

4. Set up Google OAuth:
- Place your `client_secret.json` file in the backend directory (obtain this from Google Cloud Console)

### 3. Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Generate SSL certificates for local development:
```bash
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes
```

3. Configure environment variables:
Create a `.env` file in the frontend directory:
```
REACT_APP_API_URL=https://localhost:5000
HTTPS=true
SSL_CRT_FILE=cert.pem
SSL_KEY_FILE=key.pem
```

## Running the Application

### 1. Start MongoDB
```bash
mongod --dbpath /path/to/your/data/directory
```

### 2. Start the Backend Server
```bash
cd backend
python app.py
```
The backend server will start on https://localhost:5000

### 3. Start the Frontend Development Server
```bash
cd frontend
npm start
```
The frontend will be available on https://localhost:3001

## Google Cloud Platform Setup

1. Create a new project in Google Cloud Console
2. Enable the following APIs:
   - Google Calendar API
   - Gmail API
   - People API
3. Configure OAuth consent screen
4. Create OAuth 2.0 credentials
   - Set authorized redirect URIs:
     - https://localhost:5000/oauth2callback
   - Download the client configuration file as `client_secret.json`

## Project Structure

```
backend/              # Flask backend
├── app.py           # Main application file
├── blueprints/      # Route handlers
├── config/          # Configuration files
├── models/          # Database models
├── services/        # Business logic
└── utils/           # Helper functions

frontend/            # React frontend
├── public/          # Static files
└── src/
    ├── components/  # React components
    ├── context/     # React context
    ├── hooks/       # Custom hooks
    └── utils/       # Helper functions
```

## Security Notes

- The application uses SSL/TLS for secure communication
- OAuth 2.0 is used for secure authentication
- Sensitive credentials are stored in environment variables
- MongoDB connection is secured by default configuration

## Troubleshooting

1. Certificate Issues:
   - Ensure you have valid SSL certificates
   - Accept the self-signed certificate in your browser for local development

2. MongoDB Connection:
   - Verify MongoDB is running
   - Check the connection string in .env file

3. OAuth Errors:
   - Verify redirect URIs in Google Cloud Console
   - Ensure client_secret.json is properly configured

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details
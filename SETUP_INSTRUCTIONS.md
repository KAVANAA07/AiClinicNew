# AiClinic Setup Instructions

## Quick Start (Minimal Setup)

### Backend Setup
1. Navigate to backend directory:
   ```bash
   cd ClinicProject
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. Install minimal dependencies:
   ```bash
   pip install -r requirements-minimal.txt
   ```

4. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. Create superuser:
   ```bash
   python manage.py createsuperuser
   ```

6. Start backend:
   ```bash
   python manage.py runserver
   ```

### Frontend Setup
1. Navigate to frontend directory:
   ```bash
   cd ../frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start frontend:
   ```bash
   npm start
   ```

## Full Setup (With AI Features)

If you want AI features, install the full requirements:
```bash
pip install -r requirements.txt
```

Note: This will install PyTorch and other heavy dependencies (~2GB).

## Environment Variables

Copy `.env.example` to `.env` and update with your values:
- Set `AI_BACKEND=local` for local AI processing
- Set `AI_BACKEND=hf` for Hugging Face API (requires HF_API_TOKEN)
- Set Twilio credentials for SMS (optional for development)

## Troubleshooting

### Common Issues:
1. **Import errors**: Install missing dependencies or use minimal setup
2. **Database errors**: Run migrations
3. **CORS errors**: Check frontend URL in settings.py
4. **AI errors**: Set AI_BACKEND=hf or install AI dependencies

### Development Mode:
- Backend runs on http://localhost:8000
- Frontend runs on http://localhost:3000
- Admin panel: http://localhost:8000/admin
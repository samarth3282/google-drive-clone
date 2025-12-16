# Quick Start - Local Development

## Prerequisites
- Node.js 18+ installed
- Python 3.11+ installed
- Appwrite account setup

## 1. Clone & Install

```bash
# Install Next.js dependencies
npm install

# Install Python dependencies
cd ai-agent
pip install -r requirements.txt
cd ..
```

## 2. Configure Environment

Copy `.env.example` to `.env.local`:
```bash
cp .env.example .env.local
```

Edit `.env.local` and fill in your:
- Appwrite credentials
- Google AI API key
- Vector Collection ID

## 3. Run Both Services

### Terminal 1 - Next.js Frontend
```bash
npm run dev
```
Runs on: http://localhost:3000

### Terminal 2 - FastAPI Backend
```bash
cd ai-agent
python main.py
```
Runs on: http://localhost:8000

## 4. Test

1. Open http://localhost:3000
2. Sign up / Sign in
3. Upload a file
4. Try the AI chat

---

## Deployment

Ready to deploy? Follow the comprehensive guide in [DEPLOYMENT.md](./DEPLOYMENT.md)

### Quick Deploy Commands

```bash
# Push to GitHub
git add .
git commit -m "Ready for deployment"
git push origin main

# Then follow DEPLOYMENT.md for Vercel + Render setup
```

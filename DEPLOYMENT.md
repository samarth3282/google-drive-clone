# 🚀 Deployment Guide: Vercel + Render

This guide covers deploying your Google Drive Clone with Next.js on **Vercel** and FastAPI AI Agent on **Render**.

---

## 📋 Prerequisites

1. **GitHub Account** - Your code should be pushed to GitHub
2. **Vercel Account** - Sign up at [vercel.com](https://vercel.com)
3. **Render Account** - Sign up at [render.com](https://render.com)
4. **Appwrite Account** - Sign up at [appwrite.io](https://appwrite.io)
5. **Google AI API Key** - Get from [Google AI Studio](https://aistudio.google.com/app/apikey)

---

## 🎯 Architecture Overview

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Vercel        │      │   Render         │      │   Appwrite      │
│   (Next.js)     │─────▶│   (FastAPI)      │─────▶│   (BaaS)        │
│   Port: 443     │      │   Port: 8000     │      │   Cloud         │
└─────────────────┘      └──────────────────┘      └─────────────────┘
```

---

## 📝 Part 1: Deploy FastAPI to Render

### Step 1: Create Render Web Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository: `samarth3282/google-drive-clone`
4. Configure the service:
   - **Name:** `gdrive-ai-agent`
   - **Region:** Choose closest to your users
   - **Branch:** `main`
   - **Root Directory:** `ai-agent`
   - **Runtime:** `Docker`
   - **Plan:** Start with **Free** (can upgrade later)

### Step 2: Set Environment Variables

In the Render dashboard, go to **Environment** tab and add:

```bash
# Appwrite Configuration
NEXT_PUBLIC_APPWRITE_ENDPOINT=https://cloud.appwrite.io/v1
NEXT_PUBLIC_APPWRITE_PROJECT=your_project_id_here
NEXT_PUBLIC_APPWRITE_DATABASE=your_database_id_here
NEXT_PUBLIC_APPWRITE_FILES_COLLECTION=your_files_collection_id
NEXT_PUBLIC_APPWRITE_BUCKET=your_bucket_id_here
NEXT_APPWRITE_KEY=your_api_key_here

# Google AI
GOOGLE_API_KEY=your_google_api_key_here

# Vector Collection (from Appwrite)
VECTOR_COLLECTION_ID=693fe6130028caf71954

# CORS - Keep localhost for now, update after Vercel deployment
ALLOWED_ORIGINS=http://localhost:3000
```

### Step 3: Deploy

1. Click **"Create Web Service"**
2. Wait for the build to complete (~5-10 minutes)
3. Note your service URL: `https://gdrive-ai-agent.onrender.com`

> ⚠️ **Important:** Free Render instances spin down after 15 minutes of inactivity. First request after idle will take 30-60 seconds. Upgrade to paid plan for always-on service.

---

## 📝 Part 2: Deploy Next.js to Vercel

### Step 1: Import Project

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository: `samarth3282/google-drive-clone`
4. Vercel will auto-detect Next.js configuration

### Step 2: Configure Build Settings

- **Framework Preset:** Next.js (auto-detected)
- **Root Directory:** `./` (leave default)
- **Build Command:** `npm run build` (default)
- **Output Directory:** `.next` (default)

### Step 3: Set Environment Variables

Add these in Vercel project settings → **Environment Variables**:

```bash
# Appwrite Configuration
NEXT_PUBLIC_APPWRITE_ENDPOINT=https://cloud.appwrite.io/v1
NEXT_PUBLIC_APPWRITE_PROJECT=your_project_id_here
NEXT_PUBLIC_APPWRITE_DATABASE=your_database_id_here
NEXT_PUBLIC_APPWRITE_USERS_COLLECTION=your_users_collection_id
NEXT_PUBLIC_APPWRITE_FILES_COLLECTION=your_files_collection_id
NEXT_PUBLIC_APPWRITE_BUCKET=your_bucket_id_here
NEXT_APPWRITE_KEY=your_api_key_here

# FastAPI Backend URL (from Render)
FASTAPI_URL=https://gdrive-ai-agent.onrender.com
```

### Step 4: Deploy

1. Click **"Deploy"**
2. Wait for deployment (~2-3 minutes)
3. Note your Vercel URL: `https://your-app.vercel.app`

---

## 📝 Part 3: Update CORS Configuration

Now that both services are deployed, update CORS:

### Update Render Environment Variable

1. Go to Render dashboard → Your service
2. Navigate to **Environment** tab
3. Update `ALLOWED_ORIGINS`:
   ```
   ALLOWED_ORIGINS=https://your-app.vercel.app,http://localhost:3000
   ```
4. Save changes - service will auto-redeploy

---

## 📝 Part 4: Configure Appwrite

### Enable Production Domain

1. Go to [Appwrite Console](https://cloud.appwrite.io/console)
2. Select your project
3. Go to **Settings** → **Platforms**
4. Add **Web Platform**:
   - **Name:** Production
   - **Hostname:** `your-app.vercel.app` (without https://)
5. Click **"Add Platform"**

### Verify Collections

Ensure these collections exist in your database:
- Users Collection
- Files Collection
- Vector Collection (for RAG)

---

## ✅ Testing Your Deployment

### Test FastAPI Health

```bash
curl https://gdrive-ai-agent.onrender.com/
# Expected: {"status":"AI Agent is running"}
```

### Test Next.js App

1. Visit `https://your-app.vercel.app`
2. Sign up / Sign in
3. Upload a file
4. Try the AI chat feature

---

## 🐛 Troubleshooting

### Issue: CORS Error in Browser

**Cause:** ALLOWED_ORIGINS not updated  
**Fix:** Update Render environment variable with your Vercel URL

### Issue: 401 Unauthorized from FastAPI

**Cause:** Appwrite keys mismatch  
**Fix:** Ensure same Appwrite credentials in both Vercel and Render

### Issue: Slow First Request on Render

**Cause:** Free tier spins down after inactivity  
**Solution:** 
- Upgrade to paid plan ($7/month) for always-on
- Or implement a "wake-up" ping from Vercel

### Issue: Build Failed on Render

**Cause:** Missing dependencies  
**Fix:** Check Render logs and ensure all packages in `requirements.txt`

### Issue: Next.js Build Failed on Vercel

**Cause:** TypeScript/ESLint errors  
**Fix:** Already configured to ignore in `next.config.ts`, check Vercel logs

---

## 🔒 Security Checklist

- [ ] All environment variables set correctly
- [ ] API keys are secret (not exposed in client code)
- [ ] Appwrite platform hostname configured
- [ ] CORS origins restricted to your domain
- [ ] Rate limiting enabled on Render (if available)
- [ ] Appwrite authentication rules configured

---

## 💰 Cost Estimation

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| **Vercel** | ✅ Hobby Plan (non-commercial) | $20/month Pro |
| **Render** | ✅ 750 hours/month | $7/month Starter |
| **Appwrite** | ✅ 75K executions/month | $15/month Pro |
| **Google AI** | ✅ Limited free quota | Pay-as-you-go |

**Total Free:** $0/month  
**Total Paid:** ~$42/month (if all paid tiers)

---

## 🚀 Optional Enhancements

### Add Custom Domain (Vercel)

1. Go to Vercel project settings → **Domains**
2. Add your custom domain
3. Update DNS records as instructed
4. Update ALLOWED_ORIGINS in Render

### Enable Auto-Deploy

Both Vercel and Render auto-deploy on git push to `main` branch.

### Add Monitoring

1. **Vercel Analytics:** Enable in project settings
2. **Render Logs:** View in dashboard
3. **Sentry:** Add for error tracking (optional)

### Add CI/CD

GitHub Actions workflow (optional):
```yaml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm install
      - run: npm test
```

---

## 📞 Support

- **Vercel Docs:** https://vercel.com/docs
- **Render Docs:** https://render.com/docs
- **Appwrite Docs:** https://appwrite.io/docs

---

## 🎉 Deployment Complete!

Your Google Drive Clone is now live:
- **Frontend:** https://your-app.vercel.app
- **API:** https://gdrive-ai-agent.onrender.com

Share your deployed app and enjoy! 🚀

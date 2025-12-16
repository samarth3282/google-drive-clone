# 📋 Pre-Deployment Checklist

Use this checklist before deploying to production.

---

## ✅ Code Repository

- [ ] All code committed to GitHub
- [ ] Repository is public or accessible to Vercel/Render
- [ ] Branch: `main` is up to date
- [ ] `.gitignore` excludes `.env.local` and sensitive files

---

## ✅ Environment Variables Ready

### Appwrite Setup
- [ ] Appwrite account created at https://cloud.appwrite.io
- [ ] Project created
- [ ] Database created
- [ ] Collections created:
  - [ ] Users Collection
  - [ ] Files Collection  
  - [ ] Vector Collection (for RAG)
- [ ] Storage bucket created
- [ ] API key generated (with appropriate permissions)

### Google AI
- [ ] Google AI API key obtained from https://aistudio.google.com/app/apikey
- [ ] API key tested locally

### Environment Files
- [ ] `.env.local` file configured locally (for testing)
- [ ] All values in `.env.example` documented
- [ ] Ready to input values into Vercel dashboard
- [ ] Ready to input values into Render dashboard

---

## ✅ Local Testing Complete

- [ ] Next.js runs successfully: `npm run dev`
- [ ] FastAPI runs successfully: `cd ai-agent && python main.py`
- [ ] Can sign up/login via Appwrite
- [ ] Can upload files
- [ ] Can view uploaded files
- [ ] AI chat responds correctly
- [ ] File search works
- [ ] RAG/PDF analysis works (if using this feature)

---

## ✅ Build Testing

### Next.js Build
```bash
npm run build
npm start
```
- [ ] Build completes without errors
- [ ] Production build runs correctly

### Docker Build (FastAPI)
```bash
cd ai-agent
docker build -t test-ai-agent .
docker run -p 8000:8000 --env-file ../.env.local test-ai-agent
```
- [ ] Docker image builds successfully
- [ ] Container runs without errors
- [ ] Health check passes: `curl http://localhost:8000/`

---

## ✅ Accounts Created

- [ ] Vercel account: https://vercel.com
- [ ] Render account: https://render.com
- [ ] GitHub account connected to both platforms

---

## ✅ Deployment Files Ready

- [ ] [`ai-agent/Dockerfile`](ai-agent/Dockerfile) exists
- [ ] [`ai-agent/.dockerignore`](ai-agent/.dockerignore) exists
- [ ] [`render.yaml`](render.yaml) exists
- [ ] [`.env.example`](.env.example) updated

---

## ✅ Code Verification

- [ ] No hardcoded `localhost:3000` in production code
- [ ] No hardcoded `localhost:8000` in production code
- [ ] All secrets use environment variables
- [ ] CORS configured to accept environment variable
- [ ] API routes use `FASTAPI_URL` env var

---

## ✅ Documentation Read

- [ ] Read [DEPLOYMENT.md](DEPLOYMENT.md) completely
- [ ] Understand the deployment architecture
- [ ] Know which environment variables go where
- [ ] Have Appwrite credentials ready to paste

---

## 🚀 Ready to Deploy?

If all boxes are checked, you're ready!

### Deployment Order:
1. **Deploy FastAPI to Render first** (you'll need its URL)
2. **Deploy Next.js to Vercel** (using Render URL)
3. **Update CORS** in Render with Vercel URL
4. **Test production app**

---

## 📝 Post-Deployment

After successful deployment:

- [ ] Vercel URL saved: `https://_____.vercel.app`
- [ ] Render URL saved: `https://_____.onrender.com`
- [ ] Updated `ALLOWED_ORIGINS` in Render with Vercel URL
- [ ] Added Vercel domain to Appwrite platform settings
- [ ] Tested signup/login on production
- [ ] Tested file upload on production
- [ ] Tested AI chat on production
- [ ] Shared app with users! 🎉

---

## ⚠️ If Something Fails

1. Check logs in Vercel/Render dashboard
2. Verify all environment variables are set correctly
3. Ensure Appwrite credentials match exactly
4. Check CORS configuration
5. Verify Appwrite platform hostname includes your domain
6. Review [DEPLOYMENT.md](DEPLOYMENT.md) troubleshooting section

---

**Next Step**: Go to [DEPLOYMENT.md](DEPLOYMENT.md) and start deploying! 🚀

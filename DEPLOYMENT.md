# 🚀 Render Deployment Guide

## Step-by-Step Deployment Instructions

### 1️⃣ Prepare Your Code

Make sure you have these files:
- ✅ `scrap.py` - Main application
- ✅ `requirements.txt` - Dependencies
- ✅ `Procfile` - Render config
- ✅ `runtime.txt` - Python version
- ✅ `templates/index.html` - Homepage
- ✅ `templates/results.html` - Results page
- ✅ `.gitignore` - Git ignore rules

### 2️⃣ Push to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - SEO Analyzer Pro"

# Create repository on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Push to GitHub
git push -u origin main
```

### 3️⃣ Sign Up on Render

1. Go to https://render.com
2. Click "Get Started" or "Sign Up"
3. Sign up with GitHub (recommended)
4. Authorize Render to access your repositories

### 4️⃣ Create New Web Service

1. Click **"New +"** button (top right)
2. Select **"Web Service"**
3. Choose your GitHub repository
4. Click **"Connect"**

### 5️⃣ Configure Service

Fill in these details:

**Basic Settings:**
- **Name**: `seo-analyzer-pro` (or any name you want)
- **Region**: Choose closest to your users
- **Branch**: `main`
- **Root Directory**: Leave empty
- **Environment**: `Python 3`

**Build & Deploy:**
- **Build Command**: 
  ```
  pip install -r requirements.txt
  ```
- **Start Command**: 
  ```
  uvicorn scrap:app --host 0.0.0.0 --port $PORT
  ```

**Instance Type:**
- Select **"Free"** (perfect for testing)
- Note: Free tier sleeps after 15 mins of inactivity

### 6️⃣ Environment Variables (Optional)

If you want to keep API key separate:

Click **"Advanced"** → **"Add Environment Variable"**

```
Key: GROQ_API_KEY
Value: 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
```

Then update `scrap.py`:
```python
import os
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your_fallback_key")
```

### 7️⃣ Deploy!

1. Click **"Create Web Service"**
2. Wait 2-5 minutes for build and deployment
3. Watch the logs for any errors
4. Once you see "Application startup complete", you're live! 🎉

### 8️⃣ Access Your App

Your app will be available at:
```
https://YOUR-APP-NAME.onrender.com
```

Example: `https://seo-analyzer-pro.onrender.com`

---

## ⚡ Pro Tips

### Custom Domain (Paid Plan)
- Go to Settings → Custom Domains
- Add your domain
- Update DNS records as instructed

### Auto-Deploy on Git Push
- Render auto-deploys when you push to GitHub
- No manual deployment needed!

### Monitor Your App
- Check logs in Render dashboard
- Set up email alerts for failures

### Free Tier Limitations
- Sleeps after 15 mins inactivity
- Takes 30-60 seconds to wake up
- 750 hours/month free
- Perfect for demos and testing

### Upgrade to Paid (If Needed)
- $7/month for always-on service
- Better performance
- No sleep time
- More resources

---

## 🐛 Troubleshooting

### Build Failed?
Check:
- `requirements.txt` has correct packages
- Python version in `runtime.txt` is supported
- No syntax errors in `scrap.py`

### App Not Starting?
Check:
- Start command is correct
- Port is `$PORT` (Render provides this)
- Logs for specific error messages

### 500 Internal Server Error?
Check:
- Groq API key is valid
- Templates folder exists
- All imports are correct

### Templates Not Found?
Make sure:
- `templates/` folder is committed to Git
- Folder contains `index.html` and `results.html`
- Folder name is exactly `templates` (lowercase)

---

## 📊 Performance Optimization

### For Production:
1. Use environment variables for API keys
2. Add error monitoring (Sentry)
3. Enable caching for static files
4. Use CDN for assets
5. Upgrade to paid plan for better performance

### Code Optimization:
```python
# Add caching
from functools import lru_cache

@lru_cache(maxsize=100)
def analyze_seo(url: str):
    # Your code here
    pass
```

---

## 🔄 Updating Your App

```bash
# Make changes to your code
git add .
git commit -m "Update: describe your changes"
git push origin main

# Render will auto-deploy! 🎉
```

---

## 📞 Support

**Render Documentation**: https://render.com/docs
**Render Community**: https://community.render.com/
**Status Page**: https://status.render.com/

---

## ✅ Deployment Checklist

Before deploying, make sure:

- [ ] All files are in repository
- [ ] `requirements.txt` is up to date
- [ ] Templates folder has both HTML files
- [ ] `.gitignore` excludes unnecessary files
- [ ] Tested locally with `python scrap.py`
- [ ] GitHub repository is public or Render has access
- [ ] Groq API key is valid
- [ ] Committed and pushed all changes

---

**Good luck with your deployment! 🚀**

If you face any issues, check the Render logs first - they usually tell you exactly what went wrong.

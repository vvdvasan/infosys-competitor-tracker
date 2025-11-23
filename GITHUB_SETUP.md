# Quick GitHub Setup Guide

## Step 1: Create GitHub Account (if you don't have)
1. Go to https://github.com
2. Sign up (free)
3. Verify email

## Step 2: Initialize Git in Your Project

Open terminal in your project folder:

```bash
# Initialize git
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit - E-Commerce Sentiment Analysis Dashboard"
```

## Step 3: Create GitHub Repository

1. Go to GitHub → New Repository
2. Name: `ecommerce-sentiment-analysis`
3. Description: "AI-powered sentiment analysis for e-commerce reviews using Llama 3.3 70B"
4. **IMPORTANT:** Make it **PRIVATE** (contains your API keys in .env)
5. Click "Create Repository"

## Step 4: Push Code to GitHub

Copy the commands GitHub shows you (will look like this):

```bash
git remote add origin https://github.com/YOUR_USERNAME/ecommerce-sentiment-analysis.git
git branch -M main
git push -u origin main
```

## Step 5: Add Mentor as Collaborator

1. Go to your repository
2. Settings → Collaborators
3. Add your mentor's GitHub username
4. They'll get email invitation

## Step 6: Share Link

Send your mentor:
```
GitHub Repository: https://github.com/YOUR_USERNAME/ecommerce-sentiment-analysis
```

## IMPORTANT: Before Pushing

### Create .gitignore file to exclude sensitive data:

```bash
# Create .gitignore in project root
echo .env >> .gitignore
echo __pycache__/ >> .gitignore
echo *.pyc >> .gitignore
echo venv/ >> .gitignore
echo data/database/*.db >> .gitignore
```

This prevents uploading:
- Your API keys (.env)
- Python cache files
- Virtual environment
- Database files (too large)

## Alternative: If Mentor Doesn't Have GitHub

**Option 1: Google Drive**
- Zip your project folder
- Upload to Google Drive
- Share link with "Anyone with link can view"

**Option 2: Live Demo**
- Schedule a Teams/Zoom call
- Share screen and show dashboard running
- Walk through code together

**Option 3: Loom Video**
- Record screen demo (free at loom.com)
- Show dashboard + explain code
- Share video link

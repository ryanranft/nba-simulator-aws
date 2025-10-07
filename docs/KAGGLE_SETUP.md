# Kaggle API Setup Guide

**Created:** October 6, 2025
**Purpose:** Instructions for setting up Kaggle API credentials securely

---

## ⚠️ IMPORTANT: Never Store Passwords in Code

Kaggle uses **API tokens** (not passwords) for authentication. This is more secure because:
- Tokens can be revoked without changing your password
- Tokens are separate from your login credentials
- Tokens work in scripts without exposing your password

---

## Setup Steps (5 minutes)

### Step 1: Generate Kaggle API Token

**Your Kaggle account:**
- Email: ryanranft56@gmail.com
- Password: (keep this private, don't store in files)

**Generate token:**
1. Go to: https://www.kaggle.com/settings/account
2. Log in with your credentials
3. Scroll down to "API" section
4. Click **"Create New Token"**
5. This downloads `kaggle.json` to your Downloads folder

---

### Step 2: Install Kaggle API Token

Run these commands to install the token:

```bash
# Create Kaggle config directory
mkdir -p ~/.kaggle

# Move the downloaded token (adjust path if needed)
mv ~/Downloads/kaggle.json ~/.kaggle/kaggle.json

# Set proper permissions (required by Kaggle)
chmod 600 ~/.kaggle/kaggle.json

# Verify it's there
cat ~/.kaggle/kaggle.json
```

You should see something like:
```json
{
  "username": "ryanranft56",
  "key": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

---

### Step 3: Test Kaggle API

```bash
# Activate environment
conda activate nba-aws

# Test Kaggle API
kaggle datasets list | head -5
```

If this works, you'll see a list of datasets. ✅

---

### Step 4: Download NBA Database

Now you can run the scraper:

```bash
cd /Users/ryanranft/nba-simulator-aws

# Run Kaggle database downloader
bash scripts/etl/kaggle_download.sh
```

This will:
- Download the NBA database (~2-5 GB)
- Extract to `data/kaggle/`
- Upload to S3 (optional)
- Takes 5-15 minutes

---

## Security Best Practices ✅

**What we're doing (SECURE):**
- ✅ Using API tokens (can be revoked)
- ✅ Storing tokens in `~/.kaggle/` (standard location)
- ✅ Proper file permissions (600 = only you can read)
- ✅ Token never committed to Git

**What we're NOT doing (INSECURE):**
- ❌ Storing password in code files
- ❌ Storing password in environment variables
- ❌ Committing credentials to Git
- ❌ Sharing credentials in plain text

---

## Troubleshooting

**"403 Forbidden" error:**
- Token permissions are wrong: `chmod 600 ~/.kaggle/kaggle.json`
- Token is invalid: Generate new token from Kaggle website

**"kaggle.json not found" error:**
- Token not in right location: `ls -la ~/.kaggle/`
- Move it: `mv ~/Downloads/kaggle.json ~/.kaggle/`

**"Dataset not found" error:**
- Dataset might be renamed or moved
- Check: https://www.kaggle.com/datasets/wyattowalsh/basketball

---

## Alternative: Manual Download

If API doesn't work, you can download manually:

1. Go to: https://www.kaggle.com/datasets/wyattowalsh/basketball
2. Click "Download" button
3. Extract to `data/kaggle/`
4. Point scripts at the database file

---

**Next Steps After Setup:**

Once token is installed, run:
```bash
bash scripts/etl/kaggle_download.sh
```

The database will download and be ready for validation and cross-referencing!

---

**Last Updated:** October 6, 2025
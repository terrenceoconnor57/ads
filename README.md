# Junk Removal Google Ads Campaign

This project contains a Google Ads campaign creator script and an optimized landing page.

## Structure

```
├── scripts/
│   └── create_google_ads_campaign.py  # Google Ads API campaign creator
├── landing/                            # Landing page for the ads
│   ├── index.html                      # Main HTML
│   ├── styles.css                      # Styles (mobile-responsive)
│   ├── script.js                       # Form handling
│   ├── api/
│   │   └── send-quote.js              # Vercel serverless function for email
│   ├── package.json
│   └── vercel.json
```

## Landing Page Deployment (Vercel)

### 1. Install Dependencies

```bash
cd landing
npm install
```

### 2. Set Up Resend

1. Create an account at [resend.com](https://resend.com)
2. Get your API key from the dashboard
3. Add a verified domain (or use the test domain for development)

### 3. Deploy to Vercel

```bash
# Install Vercel CLI if needed
npm install -g vercel

# Deploy from the landing directory
cd landing
vercel

# Add your Resend API key as an environment variable
vercel env add RESEND_API_KEY
```

### 4. Update Google Ads Campaign

Update `FINAL_URL` in `scripts/create_google_ads_campaign.py` with your Vercel deployment URL.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `RESEND_API_KEY` | Your Resend API key for sending form submissions |

## Features

- **Mobile-responsive design** - Works on all devices
- **Call-to-action** - Prominent phone number (201) 800-4098
- **Quote form** - Simple form that emails submissions via Resend
- **Fast loading** - Plain HTML/CSS/JS, no frameworks
- **SEO optimized** - Proper meta tags and semantic HTML

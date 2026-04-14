# Nakama Replay Viewer — Deployment Guide

## Overview

This guide walks you through deploying the Nakama Replay Viewer to **Netlify** (free).

The viewer is a **static site** — no backend required. It loads processed JSON data from the browser and renders 3D paths/heatmaps on an HTML5 canvas.

## Directory Structure

```
.
├── public/                      ← Deploy this folder to Netlify
│   ├── index.html               (main application)
│   ├── data/
│   │   ├── matches_index.json   (match metadata)
│   │   └── events_by_map.json.gz(event data, gzip compressed)
│   └── minimaps/
│       ├── AmbroseValley_Minimap.png
│       ├── GrandRift_Minimap.png
│       └── Lockdown_Minimap.jpg
├── netlify.toml                 ← Netlify config (deployment settings)
├── .gitignore                   ← Ignore large files
├── process_nakama.py            ← (stays local, not deployed)
└── February_*/                  ← (large parquet files, not deployed)
```

## Prerequisites

1. **GitHub account** (free) — for git hosting + easy Netlify integration
2. **Netlify account** (free) — sign up at https://netlify.com

## Step-by-Step Deployment

### 1. Initialize a Git Repository

```bash
cd /path/to/player_data
git init
git config user.name "Your Name"
git config user.email "your-email@example.com"
```

### 2. Stage Files for Commit

```bash
git add public/
git add netlify.toml
git add .gitignore
git add README.md
git add process_nakama.py        # (optional, for reference)
```

### 3. Create Your First Commit

```bash
git commit -m "Initial commit: Nakama Replay Viewer

- Static HTML5 canvas app for viewing game replays
- Data: 796 matches across 3 maps (Feb 10-14)
- Ready to deploy to Netlify"
```

### 4. Create a GitHub Repository

1. Go to https://github.com/new
2. **Repository name:** `nakama-replay-viewer` (or your choice)
3. **Description:** "Interactive game replay viewer"
4. **Public** (if you want anyone to access it)
5. Click "Create repository"

### 5. Push Your Code to GitHub

GitHub will show you instructions. They'll look something like:

```bash
git remote add origin https://github.com/YOUR_USERNAME/nakama-replay-viewer.git
git branch -M main
git push -u origin main
```

Copy and run these commands in your terminal.

### 6. Deploy to Netlify

**Option A: Connect GitHub (Recommended)**

1. Go to https://netlify.com and sign in
2. Click **"New site from Git"** or **"Import an existing project"**
3. Choose **GitHub** as your git provider
4. Authorize Netlify to access your GitHub account
5. Select your `nakama-replay-viewer` repository
6. **Build settings:**
   - Build command: *(leave empty — no build needed)*
   - Publish directory: `public`
7. Click **"Deploy site"**

Netlify will automatically deploy from your `main` branch. You'll get a site URL like:
```
https://your-site-name.netlify.app
```

**Option B: Manual Deploy (Drag & Drop)**

1. Go to https://netlify.com/drop
2. Drag the `public/` folder onto Netlify
3. You'll get a temporary site URL instantly

### 7. Verify Deployment

1. Visit your Netlify URL
2. Try selecting a map, date, and match
3. Test zoom/pan, stat details modal, heatmap view, etc.
4. Check browser console (F12) for errors

## Updating the Replay Data

If you **reprocess** the parquet files and get new `matches_index.json` and `events_by_map.json.gz`:

```bash
# Copy new data to public/
cp output/matches_index.json public/data/
cp output/events_by_map.json.gz public/data/

# Commit & push
git add public/data/
git commit -m "Update: new replay data (N matches, M events)"
git push

# Netlify auto-deploys!
```

## Performance Notes

- **Data file size:** ~2.7 MB (gzipped). Loads on demand per match.
- **Minimap images:** ~24 MB total. Cached by browser and Netlify CDN.
- **JavaScript:** ~99 KB (index.html). No external dependencies (uses pako.js from CDN for gzip).

## Troubleshooting

### "Could not load matches_index.json"
- In browser console (F12), check if the path is correct
- Verify `public/data/matches_index.json` exists on Netlify
- Try a hard refresh (Ctrl+Shift+R)

### Heatmap rendering is slow / canvas freezes
- This happens on large matches with 1000+ events
- The viewer caches data after first load
- Try zooming in to reduce points drawn
- Check your browser's WebGL support (F12 → Console)

### Images not loading
- Verify minimap files exist: `public/minimaps/*.png` and `*.jpg`
- Check file names match exactly (case-sensitive)
- Netlify CDN cache may need clearing (try hard refresh)

## Custom Domain (Optional)

1. In Netlify dashboard, go to **Site Settings** → **Domain Management**
2. Click **"Add custom domain"**
3. Enter your domain (e.g., `replays.example.com`)
4. Follow DNS setup instructions for your domain registrar

## Further Reading

- [Netlify Docs](https://docs.netlify.com/)
- [GitHub Getting Started](https://docs.github.com/en/get-started)

---

**Questions?** Check the browser console (F12) for errors, or review the HTML file's comments.

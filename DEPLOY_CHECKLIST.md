# Deployment Checklist

## Pre-Deployment ✅
- [x] All files in `public/` folder ready
  - [x] index.html (99 KB)
  - [x] data/matches_index.json (145 KB)
  - [x] data/events_by_map.json.gz (2.7 MB)
  - [x] minimaps/ with 3 map images (24 MB total)

## GitHub Setup
- [ ] Create GitHub account at https://github.com/signup (if not already)
- [ ] Create new repository: https://github.com/new
  - Name: `nakama-replay-viewer`
  - Make it **Public**
  - Click "Create repository"

## Local Git Commands
From your `/sessions/sharp-festive-wright/mnt/player_data/` directory:

```bash
# Only run ONCE (initialize git):
git init
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Add all files:
git add .

# Commit:
git commit -m "Initial commit: Nakama Replay Viewer"

# Connect to GitHub (use YOUR URL from GitHub):
git remote add origin https://github.com/YOUR_USERNAME/nakama-replay-viewer.git
git branch -M main
git push -u origin main
```

## Netlify Deployment
- [ ] Sign up at https://netlify.com (free account)
- [ ] Go to https://app.netlify.com
- [ ] Click "New site from Git"
- [ ] Select **GitHub** → Authorize → Choose your repo
- [ ] Build settings:
  - **Publish directory:** `public`
  - **Build command:** (leave empty)
  - Click **"Deploy"**
- [ ] Wait 1-2 minutes for deployment
- [ ] Click your site URL to test!

## Testing
- [ ] Site loads without errors
- [ ] Can select Map, Date, Match
- [ ] Paths view renders correctly
- [ ] Heatmap view works
- [ ] Zoom/pan functional
- [ ] Stat details modal opens
- [ ] Hot zones clickable

## Done! 🎉
Your viewer is live at: `https://your-site-name.netlify.app`

---

**File sizes for reference:**
- public/index.html: 99 KB
- public/data/: ~2.8 MB (gzipped)
- public/minimaps/: ~24 MB
- **Total deployed:** ~27 MB

**Caching:**
- HTML: no-cache (always fresh)
- Data: 24 hours
- Images: 7 days

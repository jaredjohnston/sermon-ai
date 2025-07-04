# Frontend-Backend Migration Plan

## 🤔 **The Question**
Should I migrate my `sermon-ai-web` repo into my `sermon_ai` backend repo to create a monorepo?

## 🎯 **UPDATED RECOMMENDATION: Monorepo + v0 Integration** ✅

**Great news!** After researching Vercel v0, you **CAN** change repositories and keep the slick v0 workflow.

### **Why Monorepo Makes Sense for Your Case:**
- ✅ **You're solo/small team** - easier management
- ✅ **Shared TypeScript types** - true type safety between frontend/backend
- ✅ **Faster iteration** - change backend API + frontend in one commit
- ✅ **Simpler deployment** - one Docker setup for everything
- ✅ **Startup-friendly** - most successful startups use monorepos early on
- ✅ **v0 can be reconnected** - you don't lose the smooth workflow!

## 🏗️ **Final Structure**
```
sermon_ai/                    # Root repo
├── backend/                  # Move existing app/ here
│   ├── app/
│   ├── requirements.txt
│   ├── main.py
│   └── ...
├── frontend/                 # Migrated sermon-ai-web
│   ├── src/
│   ├── package.json
│   └── ...
├── shared/                   # New shared directory
│   ├── types/               # Shared TypeScript interfaces
│   └── configs/
├── docker-compose.yml       # Full stack setup
├── README.md               # Updated for monorepo
└── .gitignore              # Combined ignores
```

## 🔧 **Migration Steps**

### **Phase 1: Backend Repository Setup**
```bash
# In your local sermon_ai directory
cd /Users/jaredjohnston/sermon_ai

# 1. Backup everything first!
cp -r /Users/jaredjohnston/sermon_ai /Users/jaredjohnston/sermon_ai_backup

# 2. Commit current changes
git status  # See what changes need to be committed first
git add .
git commit -m "feat: complete custom content template system"

# 3. Create and push develop branch to remote
git checkout develop  # (if not already on develop)
git push -u origin develop

# 4. Merge develop to main for the "big migration"
git checkout main
git merge develop
git push origin main
```

### **Phase 2: Frontend Migration** 
```bash
# Still in sermon_ai directory
mkdir frontend/
cd frontend/

# Clone frontend repo into the frontend folder
git clone https://github.com/jaredjohnston/sermon-ai-web.git .

# Remove the git history (we'll use the parent repo's git)
rm -rf .git

# Go back to parent directory
cd ..

# Add frontend to main repo
git add frontend/
git commit -m "feat: migrate frontend into monorepo structure

- Integrate sermon-ai-web into main repository
- Set up monorepo structure for better development workflow
- Shared types and configs between frontend/backend"

git push origin main
```

### **Phase 3: Reorganization (Optional but recommended)**
```bash
# Move backend files into backend/ subdirectory
mkdir backend/
mv app/ requirements.txt main.py *.py backend/

# Create shared directory
mkdir shared/
mkdir shared/types/
mv frontend-types.ts shared/types/api.ts

# Update all import paths in both frontend and backend
```

## ✅ **SOLUTION: v0 Repository Switching**

### **Research Findings:**
After researching Vercel v0, I discovered you **CAN** change the GitHub repository that v0 points to!

**Process:**
1. Go to your v0 project in Vercel Dashboard
2. Navigate to **Settings** → **Git**  
3. Click **"Disconnect"** to detach current repo
4. Connect to your new monorepo
5. Set **Root Directory** to `frontend/` in project settings

### **This Means:**
- ✅ **Keep v0's slick workflow** - no manual syncing needed
- ✅ **Work from same codebase** - perfect for collaboration  
- ✅ **Shared types** between frontend/backend
- ✅ **Single source of truth** for the entire project

## 🚀 **NEW RECOMMENDED APPROACH: Full Migration**

Go ahead with the monorepo migration! You can have both:
- **Collaborative development** (same repo)
- **Smooth v0 experience** (reconnect after migration)

## 📋 **UPDATED Action Plan: Full Migration**

### **Phase 1: Complete Monorepo Migration (Today)**
1. ✅ Backup everything: `cp -r sermon_ai sermon_ai_backup`
2. ✅ Commit current backend changes
3. ✅ Push develop branch to GitHub: `git push -u origin develop`
4. ✅ Merge develop → main: Full backend migration
5. ✅ Migrate frontend into monorepo structure
6. ✅ Test that everything builds locally

### **Phase 2: Reconnect v0 (Today/Tomorrow)**
1. ✅ Go to Vercel Dashboard → Your v0 project
2. ✅ Settings → Git → "Disconnect" from sermon-ai-web
3. ✅ Connect to new monorepo: `github.com/jaredjohnston/sermon_ai`
4. ✅ Set **Root Directory** to `frontend/` in project settings
5. ✅ Test that v0 can still push changes smoothly

### **Phase 3: Development Integration (This Week)**
1. ✅ Set up shared types in `shared/types/api.ts`
2. ✅ Update frontend to use backend API endpoints
3. ✅ Test onboarding flow end-to-end
4. ✅ Integrate authentication flow

### **Phase 4: Production Setup (Next Week)**
1. ✅ Set up Docker Compose for full stack
2. ✅ Configure deployment pipeline
3. ✅ Test production build

## 🎯 **Key Benefits You'll Get**

### **Immediate:**
- **Same codebase** for collaboration
- **Shared TypeScript types** (no more copy-paste)
- **Atomic commits** (change API + frontend together)

### **v0 Integration:**
- **Keep the slick workflow** you love
- **No manual syncing** required
- **v0 continues to work** exactly as before

## 📝 **Notes for Tomorrow**

### **Success Criteria:**
- ✅ Backend and frontend in same repo
- ✅ v0 still pushes changes smoothly
- ✅ Shared types working between frontend/backend
- ✅ Local development environment working

### **Fallback Plan:**
If v0 reconnection has issues:
- Keep monorepo for development
- Set up manual sync script as backup
- Most benefits still achieved

## 🎉 **Final Thought**
This is the best of both worlds! You get collaborative development benefits AND keep the v0 workflow you love. The research shows this approach is totally feasible.
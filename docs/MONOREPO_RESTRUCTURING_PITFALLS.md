# Monorepo Restructuring: Common Mistakes and Pitfalls

## 🚨 **Critical Don'ts**

### **Virtual Environments & Dependencies**

❌ **DON'T** move source code without rebuilding virtual environments
- Virtual environments contain absolute paths to your source code
- Moving Python files breaks import resolution silently
- **DO:** Delete and recreate venv after restructuring

❌ **DON'T** commit virtual environments to git
```bash
# Bad
git add venv/
git add env/
git add .venv/

# Good
echo "venv/" >> .gitignore
echo "env/" >> .gitignore
echo ".venv/" >> .gitignore
```

❌ **DON'T** interrupt package installations during restructuring
- Ctrl+C during `pip install` can corrupt package metadata
- **DO:** Complete installations or start fresh with clean venv

❌ **DON'T** assume dependencies will "just work" in new structure
- Different package managers have different path resolution
- **DO:** Test imports after every major structural change

### **Directory Structure & File Movement**

❌ **DON'T** move files gradually while keeping services running
```bash
# Bad - moving files while server is running
mv app/ backend/app/  # Server still trying to import from old location
python run.py  # Fails silently
```

❌ **DON'T** create nested duplicate structures
```bash
# Bad - confusing hierarchy
project/
├── app/           # Old structure
├── backend/
│   └── app/       # New structure - same name!
└── frontend/
```

❌ **DON'T** move configuration files without updating references
- `.env` files with relative paths
- `requirements.txt` with local package references
- Config files with hardcoded paths

### **Import Statements & Module Resolution**

❌ **DON'T** use relative imports across package boundaries
```python
# Bad - breaks when restructuring
from ../shared.utils import helper
from ../../backend.services import api

# Good - absolute imports from package root
from shared.utils import helper
from backend.services import api
```

❌ **DON'T** hardcode module paths in Python code
```python
# Bad
sys.path.append('/absolute/path/to/my/project/backend')

# Good
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
```

### **Build Systems & Package Management**

❌ **DON'T** mix package managers without coordination
```bash
# Bad - conflicting package managers
backend/requirements.txt   # pip
frontend/package.json      # npm
shared/poetry.lock         # poetry
root/Pipfile              # pipenv
```

❌ **DON'T** forget to update build scripts and CI/CD
- Docker build contexts need updating
- GitHub Actions paths need revision
- Deploy scripts often hardcode paths

### **Version Control & Git**

❌ **DON'T** commit large restructuring changes in one massive commit
```bash
# Bad
git add .
git commit -m "restructure everything"

# Good - atomic commits
git commit -m "move backend code to backend/ directory"
git commit -m "update import statements for new structure"
git commit -m "fix build scripts for monorepo"
```

❌ **DON'T** ignore gitignore updates
- Old `.gitignore` patterns may not work in new structure
- Build artifacts might end up in wrong locations
- IDE files might scatter across subdirectories

❌ **DON'T** lose track of which branch/commit was last working
```bash
# Good practice - tag working states
git tag -a "pre-monorepo-working" -m "Last working state before restructuring"
```

## ⚠️ **Common Pitfalls**

### **1. Path Resolution Hell**

**Problem:** Imports work in development but break in production
```python
# Works locally but breaks when deployed
from app.services import database  # Can't find 'app' module
```

**Solution:** Use consistent package structure and proper Python packaging

### **2. Environment Variable Confusion**

**Problem:** `.env` files with relative paths stop working
```bash
# Bad - breaks when files move
DATABASE_CONFIG_PATH=./config/database.yaml

# Good - use absolute paths or environment-aware resolution
DATABASE_CONFIG_PATH=${PROJECT_ROOT}/backend/config/database.yaml
```

### **3. Docker Build Context Issues**

```dockerfile
# Bad - assumes flat structure
COPY requirements.txt .
COPY app/ ./app/

# Good - explicit about monorepo structure
COPY backend/requirements.txt .
COPY backend/app/ ./app/
```

### **4. IDE Configuration Drift**

**Problem:** IDE settings become inconsistent across team
- VSCode settings scattered in multiple `.vscode/` folders
- Python path configurations pointing to old locations
- Linting rules not applying consistently

### **5. Testing Path Problems**

```python
# Bad - tests break when code moves
import sys
sys.path.append('../src')  # Assumes specific directory structure

# Good - robust test setup
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
```

## ✅ **Best Practices**

### **Before You Start**

1. **Create a working backup**
   ```bash
   git tag "pre-restructure-backup"
   cp -r project/ project_backup/
   ```

2. **Document current working state**
   - How to run the application
   - What commands currently work
   - Environment setup steps

3. **Plan the target structure first**
   ```
   monorepo/
   ├── backend/
   │   ├── src/
   │   ├── tests/
   │   ├── requirements.txt
   │   └── Dockerfile
   ├── frontend/
   │   ├── src/
   │   ├── package.json
   │   └── Dockerfile
   ├── shared/
   │   └── types/
   └── docs/
   ```

### **During Restructuring**

1. **Work in small, testable chunks**
   - Move one component at a time
   - Test after each move
   - Commit working states frequently

2. **Update imports immediately after moves**
   - Don't let broken imports accumulate
   - Use IDE refactoring tools when possible

3. **Rebuild virtual environments early and often**
   ```bash
   rm -rf venv/
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   # Test imports
   python -c "from backend.app.main import app; print('Success!')"
   ```

### **After Restructuring**

1. **Clean up orphaned files**
   ```bash
   find . -name "__pycache__" -exec rm -rf {} +
   find . -name "*.pyc" -delete
   find . -name ".DS_Store" -delete
   ```

2. **Update all documentation**
   - README.md with new setup instructions
   - Development environment setup
   - Build and deployment procedures

3. **Verify everything works from scratch**
   - Clone repo to new directory
   - Follow setup instructions exactly
   - Run all tests and main functionality

## 🔧 **Recovery Strategies**

### **When Things Go Wrong**

1. **Environment corruption (like you experienced)**
   ```bash
   # Nuclear option - rebuild everything
   rm -rf venv/ node_modules/
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Import resolution broken**
   ```bash
   # Debug Python path issues
   python -c "import sys; print('\\n'.join(sys.path))"
   python -c "import your_module"  # Test specific imports
   ```

3. **Rollback strategy**
   ```bash
   # Return to last known working state
   git reset --hard pre-restructure-backup
   git clean -fd  # Remove untracked files
   ```

## 📚 **Additional Resources**

- **Monorepo Tools:** Nx, Lerna, Rush, Bazel
- **Python Packaging:** `setuptools`, `poetry`, proper `__init__.py` usage
- **Docker Multi-stage builds** for monorepo deployments
- **CI/CD patterns** for monorepo testing and deployment

---

**Remember:** Monorepo restructuring is a major architectural change. Take it slow, test frequently, and always have a rollback plan!
@echo off
echo 🚀 Updating GitHub Repository...
echo =================================

echo 📊 Checking git status...
git status

echo.
echo 📦 Adding all changes...
git add --all

echo.
echo 💾 Committing changes...
git commit -m "🚀 COMPLETE RENDER.COM DEPLOYMENT

• Added main_render.py with FastAPI web interface
• Added requirements.txt with all dependencies
• Added render.yaml for Render.com configuration
• Updated all trading logic with phase-wise TSL
• Fixed smart entry with real market integration
• Added webhook support for Flattrade
• Ready for live trading deployment"

echo.
echo 📤 Pushing to GitHub...
git push origin main

echo.
echo ✅ GitHub update complete!
echo 🌐 Check: https://github.com/YOUR_USERNAME/YOUR_REPO
echo.
pause
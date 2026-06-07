#!/bin/bash
# deploy.sh - Deploy outreach-pipeline to GitHub and Render
# Usage: ./deploy.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Outreach Pipeline Deployment Script  ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: Run this script from the outreach-pipeline directory${NC}"
    exit 1
fi

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}Initializing git repository...${NC}"
    git init
    git branch -m main
fi

# Stage all changes
echo -e "${YELLOW}Staging changes...${NC}"
git add -A

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo -e "${GREEN}No changes to commit${NC}"
else
    echo -e "${YELLOW}Committing changes...${NC}"
    git commit -m "Deploy: $(date '+%Y-%m-%d %H:%M:%S')"
fi

# Check GitHub CLI authentication
echo ""
echo -e "${YELLOW}Checking GitHub authentication...${NC}"
if ! gh auth status &>/dev/null; then
    echo -e "${YELLOW}GitHub CLI not authenticated. Starting login...${NC}"
    echo ""
    echo -e "${GREEN}A browser window will open. Please:${NC}"
    echo "  1. Log in with your GitHub account"
    echo "  2. Authorize the GitHub CLI"
    echo ""
    gh auth login
fi

echo -e "${GREEN}✓ GitHub authenticated${NC}"

# Check if remote exists
REPO_NAME="outreach-pipeline"
GITHUB_USER=$(gh api user -q .login 2>/dev/null || echo "")

if [ -z "$GITHUB_USER" ]; then
    echo -e "${RED}Could not get GitHub username${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Logged in as: $GITHUB_USER${NC}"

# Check if repo exists on GitHub
if ! gh repo view "$GITHUB_USER/$REPO_NAME" &>/dev/null; then
    echo -e "${YELLOW}Creating GitHub repository...${NC}"
    gh repo create "$REPO_NAME" --public --source=. --remote=origin --push
    echo -e "${GREEN}✓ Repository created and code pushed${NC}"
else
    echo -e "${GREEN}✓ Repository exists${NC}"
    
    # Check if origin remote is set
    if ! git remote get-url origin &>/dev/null; then
        git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"
    fi
    
    echo -e "${YELLOW}Pushing to GitHub...${NC}"
    git push -u origin main
    echo -e "${GREEN}✓ Code pushed to GitHub${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  GitHub Deployment Complete!          ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Repository: ${GREEN}https://github.com/$GITHUB_USER/$REPO_NAME${NC}"
echo ""

# Render deployment instructions
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  Next: Deploy to Render.com           ${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo "To deploy on Render:"
echo ""
echo "  1. Go to: https://dashboard.render.com/select-repo?type=web"
echo "  2. Connect your GitHub account (if not already)"
echo "  3. Select: $GITHUB_USER/$REPO_NAME"
echo "  4. Configure:"
echo "     - Name: outreach-pipeline"
echo "     - Runtime: Python 3"
echo "     - Build Command: pip install -e ."
echo "     - Start Command: python -m outreach_pipeline --help"
echo ""
echo "  5. Add Environment Variables:"
echo "     - OCEAN_API_KEY"
echo "     - PROSPEO_API_KEY"
echo "     - EAZYREACH_API_KEY"  
echo "     - BREVO_API_KEY"
echo "     - SENDER_NAME"
echo "     - SENDER_EMAIL"
echo ""
echo -e "${GREEN}Done! Your code is on GitHub and ready for Render.${NC}"

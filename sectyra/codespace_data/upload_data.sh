#!/bin/bash
set -e

if [ -f "/home/codespace/codespace_data/.env" ]; then
    source "/home/codespace/codespace_data/.env"
fi

if [ -z "$PATH_RESULTS" ]; then
    echo "❌ Error: PATH_RESULTS is not set." | notify -silent
    exit 1
fi

if [ ! -d "$PATH_RESULTS" ]; then
    echo "❌ Error: PATH_RESULTS directory does not exist." | notify -silent
    exit 1
fi

TEMP_REPO_DIR="/home/codespace/temp_results_repo"
rm -rf "$TEMP_REPO_DIR"
mkdir -p "$TEMP_REPO_DIR"

CODESPACE_NAME="$(cat /opt/.code_name)"
COMMIT_MESSAGE="Upload results on $(date -u +"%Y-%m-%dT%H:%M:%SZ")"

git config --global user.email "${GIT_EMAIL:-user@example.com}"
git config --global user.name "${GIT_USERNAME:-GitHub User}"

set +e
git clone "https://${GIT_TOKEN}@github.com/${GITHUB_USERNAME}/${RESULTS_REPO}.git" "$TEMP_REPO_DIR"
CLONE_STATUS=$?
set -e
if [ $CLONE_STATUS -ne 0 ]; then
    echo "❌ Error: Failed to clone the repository." | notify -silent
    rm -rf "$TEMP_REPO_DIR"
    exit 1
fi

if [ ! -f "$TEMP_REPO_DIR/.gitignore" ]; then
    cat > "$TEMP_REPO_DIR/.gitignore" << EOL
.DS_Store
Thumbs.db
desktop.ini
*.log
logs/
*.tmp
*.temp
*.swp
*~
.cache/
__pycache__/
*.py[cod]
*$py.class
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
node_modules/
vendor/
EOL
fi

cp -r "$PATH_RESULTS"/* "$TEMP_REPO_DIR/"

cd "$TEMP_REPO_DIR"
git add -A

if git diff --staged --quiet; then
    echo "❌ Nothing to commit. No new results to upload." | notify -silent
else
    set +e
    git commit -m "$COMMIT_MESSAGE"
    COMMIT_STATUS=$?
    set -e
    if [ $COMMIT_STATUS -ne 0 ]; then
        echo "❌ Error: Failed to commit results." | notify -silent
        rm -rf "$TEMP_REPO_DIR"
        exit 1
    fi

    set +e
    git push
    PUSH_STATUS=$?
    set -e
    if [ $PUSH_STATUS -ne 0 ]; then
        echo "❌ Error: Failed to push results to the repository." | notify -silent
        rm -rf "$TEMP_REPO_DIR"
        exit 1
    fi

    echo "✅ Results have been successfully uploaded to the repository." | notify -silent
fi

rm -rf "$TEMP_REPO_DIR"

gh cs delete -c $CODESPACE_NAME

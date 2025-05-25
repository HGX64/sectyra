#!/bin/bash
set -euo pipefail

ROOT_DIR="/home/codespace/codespace_data"
JOBS_DIR="$ROOT_DIR/jobs"
CODESPACE_NAME="$(cat /opt/.code_name)"
CODESPACE_ID="$(cat /opt/.code_id)"
RANDOM_NAME="$(head /dev/urandom | tr -dc 'a-z' | head -c 8)"
CURRENT_JOB="$JOBS_DIR/job.sh.$CODESPACE_ID"

set -a
source "$ROOT_DIR/.env"
set +a


echo "✅ Running job: *$(cat /opt/.code_id)*" | notify -silent

if ! bash "$CURRENT_JOB" 2>/home/codespace/runner.log; then
  echo "❌ Job $(cat /opt/.code_id) failed, The codespace will be deleted in 5 minutes!" | notify -silent 2>/home/codespace/notify.log

  (
    sleep 300
    echo "🗑️ Deleting codespace after job failure: $CODESPACE_NAME" | notify -silent 2>/home/codespace/notify_2.log
    gh codespace delete -c "$CODESPACE_NAME"
  ) &

  exit 1
fi

NEW_CODE_ID=$((CODESPACE_ID + 1))
NEXT_JOB="$JOBS_DIR/job.sh.$NEW_CODE_ID"

if [[ -f "$NEXT_JOB" ]]; then
  gh codespace create --repo "$CODE_REPO" --machine basicLinux32gb --display-name "$RANDOM_NAME"
  sleep 3

  COMPLETE_NEW_NAME="$(gh codespace list | awk '{print $1}' | grep "$RANDOM_NAME")"

  (cd /home/codespace && zip -r "/home/codespace/code_data.zip" codespace_data)

  echo "$COMPLETE_NEW_NAME"

  ZIP_BASE64=$(base64 -w 0 /home/codespace/code_data.zip)

  SCRIPT_CONTENT=$(cat <<EOF
#!/bin/bash
set -euo pipefail

# Decodificar zip embebido
cat <<'ARCHIVE_END' | base64 -d > /home/codespace/code_data.zip
$ZIP_BASE64
ARCHIVE_END

unzip -o /home/codespace/code_data.zip -d /home/codespace/
rm /home/codespace/code_data.zip


sudo apt update && sudo apt install -y cron tmux curl

echo "$COMPLETE_NEW_NAME" | sudo tee /opt/.code_name > /dev/null
echo "$NEW_CODE_ID" | sudo tee /opt/.code_id > /dev/null

set -a
source /home/codespace/codespace_data/.env
set +a

grep -qxF "source /home/codespace/codespace_data/.env" /home/codespace/.bashrc || echo "source /home/codespace/codespace_data/.env" >> /home/codespace/.bashrc

echo "\$GIT_TOKEN" | gh auth login --hostname github.com --with-token
sleep 2

sudo bash -c 'cat /home/codespace/codespace_data/crontab >> /etc/crontab'

sudo service cron start

cd /opt 
curl -LO https://github.com/projectdiscovery/notify/releases/download/v1.0.7/notify_1.0.7_linux_amd64.zip 
unzip -o notify_1.0.7_linux_amd64.zip 
sudo mv notify /usr/bin/notify
mkdir -p /home/codespace/.config/notify

sleep 2 

envsubst < /home/codespace/codespace_data/.notify.yaml > /home/codespace/.config/notify/provider-config.yaml

sleep 2

chmod +x /home/codespace/codespace_data/runner.sh
cd /home/codespace/codespace_data
sudo ./runner.sh &> /home/codespace/runner_output.log
EOF
)

  echo "$SCRIPT_CONTENT" | gh codespace ssh -c "$COMPLETE_NEW_NAME" -- 'cat > /home/codespace/remote_install.sh && chmod +x /home/codespace/remote_install.sh'

  gh codespace ssh -c "$COMPLETE_NEW_NAME" -- "sudo apt update && sudo apt install tmux -y"
  sleep 3

  gh codespace ssh -c "$COMPLETE_NEW_NAME" -- 'tmux new-session -d -s setup_runner "/home/codespace/remote_install.sh"'

  gh codespace delete -c "$CODESPACE_NAME"

else
  bash "$ROOT_DIR/upload_data.sh"
fi


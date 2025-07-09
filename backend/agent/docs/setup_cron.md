# Azure SQL 자동 설정 Cron Job 가이드

## 1. Cron Job 설정 방법

### 매일 오전 9시에 Azure SQL 리소스 재생성
```bash
# cron job 편집
crontab -e

# 다음 줄 추가 (매일 오전 9시)
0 9 * * * /Users/kdb/ms_final_mvp/backend/agent/cron_setup_azure.sh

# 또는 매일 오전 8시 30분
30 8 * * * /Users/kdb/ms_final_mvp/backend/agent/cron_setup_azure.sh
```

### 주중(월-금) 오전 9시에만 실행
```bash
# 주중에만 실행
0 9 * * 1-5 /Users/kdb/ms_final_mvp/backend/agent/cron_setup_azure.sh
```

### 매주 월요일 오전 9시에 실행
```bash
# 매주 월요일에만 실행
0 9 * * 1 /Users/kdb/ms_final_mvp/backend/agent/cron_setup_azure.sh
```

## 2. 현재 설정된 Cron Job 확인
```bash
# 현재 cron job 목록 확인
crontab -l

# cron job 로그 확인
tail -f /var/log/cron.log
```

## 3. 로그 파일 확인
```bash
# 자동 생성된 로그 파일 확인
ls -la /tmp/azure_sql_setup_*.log

# 최신 로그 파일 내용 확인
tail -f /tmp/azure_sql_setup_$(date +%Y%m%d).log
```

## 4. 수동 테스트
```bash
# cron job 스크립트 수동 실행
cd /Users/kdb/ms_final_mvp/backend/agent
./cron_setup_azure.sh
```

## 5. 환경 변수 자동 적용
자동 설정 완료 후 환경 변수를 적용하려면:

```bash
# 자동 생성된 환경 변수 설정 스크립트 실행
source /Users/kdb/ms_final_mvp/backend/agent/set_azure_env.sh

# 또는 Python 스크립트로 환경 변수 설정
python3 /Users/kdb/ms_final_mvp/backend/agent/azure_sql_config.py
```

## 6. 시스템 시작 시 자동 실행 (LaunchAgent)
macOS에서 시스템 시작 시 자동으로 Azure SQL 설정을 실행하려면:

```bash
# LaunchAgent 설정 파일 생성
cat > ~/Library/LaunchAgents/com.kdb.azure-sql-setup.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.kdb.azure-sql-setup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/kdb/ms_final_mvp/backend/agent/cron_setup_azure.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/azure_sql_setup.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/azure_sql_setup_error.log</string>
</dict>
</plist>
EOF

# LaunchAgent 로드
launchctl load ~/Library/LaunchAgents/com.kdb.azure-sql-setup.plist

# LaunchAgent 언로드 (필요시)
launchctl unload ~/Library/LaunchAgents/com.kdb.azure-sql-setup.plist
```

## 7. 알림 설정 (선택사항)
Slack이나 이메일 알림을 받으려면 `cron_setup_azure.sh` 파일의 마지막 부분에 다음 추가:

```bash
# Slack 알림 (Webhook URL 필요)
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Azure SQL 자동 설정 완료 - '"$(date)"'"}' \
  https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# 이메일 알림 (mail 명령어 필요)
echo "Azure SQL 자동 설정 완료 - $(date)" | mail -s "Azure SQL Setup Complete" your-email@example.com
```

## 8. 문제 해결
- cron job이 실행되지 않는 경우: `crontab -e`에서 경로를 절대 경로로 지정
- Azure 로그인 문제: 서비스 주체 설정 또는 `az login --use-device-code` 사용
- 권한 문제: 스크립트 파일에 실행 권한 확인 (`chmod +x`)

## 9. 실행 권한 설정
```bash
# 모든 스크립트에 실행 권한 부여
chmod +x /Users/kdb/ms_final_mvp/backend/agent/setup_azure_sql_auto.sh
chmod +x /Users/kdb/ms_final_mvp/backend/agent/cron_setup_azure.sh  
chmod +x /Users/kdb/ms_final_mvp/backend/agent/quick_setup.sh
``` 
#!/bin/bash
# chaos_test.sh — kills a container and measures detection + recovery time
# Usage: bash chaos_test.sh [container_name]

TARGET=${1:-devops-container}
TIMEOUT=60

echo "🔥 Chaos Test: killing $TARGET"
KILL_TIME=$(date +%s)
docker kill "$TARGET" > /dev/null 2>&1

echo "⏳ Waiting for recovery (max ${TIMEOUT}s)..."
for i in $(seq 1 $TIMEOUT); do
  sleep 1
  STATUS=$(docker inspect "$TARGET" --format='{{.State.Status}}' 2>/dev/null)
  if [ "$STATUS" = "running" ]; then
    RECOVERY_TIME=$(( $(date +%s) - KILL_TIME ))
    echo ""
    echo "✅ Recovery Report"
    echo "----------------------------"
    echo "Container     : $TARGET"
    echo "Detection+Fix : ${RECOVERY_TIME}s"
    echo "Status        : running"
    echo "----------------------------"
    exit 0
  fi
  printf "."
done

echo ""
echo "❌ $TARGET did not recover within ${TIMEOUT}s"
exit 1

#!/bin/bash
# WINDI Command Bridge — Startup Script
# Usage: bash start_bridge.sh [start|stop|restart|status|logs]

BRIDGE_DIR="/opt/windi/bridge"
PID_FILE="/tmp/command_bridge.pid"
LOG_FILE="/opt/windi/logs/command_bridge.log"
ENV_FILE="${BRIDGE_DIR}/.env"

# Load environment
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

start() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "Bridge already running (PID $(cat $PID_FILE))"
        return 1
    fi
    
    echo "Starting WINDI Command Bridge on port ${WINDI_BRIDGE_PORT:-8097}..."
    cd "$BRIDGE_DIR"
    nohup python3 command_bridge.py serve > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 2
    
    if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "✅ Bridge started (PID $(cat $PID_FILE))"
        echo "   Log: $LOG_FILE"
        echo "   Health: curl http://localhost:${WINDI_BRIDGE_PORT:-8097}/health"
    else
        echo "❌ Bridge failed to start. Check: tail -20 $LOG_FILE"
        return 1
    fi
}

stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            rm -f "$PID_FILE"
            echo "✅ Bridge stopped (was PID $PID)"
        else
            rm -f "$PID_FILE"
            echo "Bridge was not running (stale PID file removed)"
        fi
    else
        # Try to find and kill by name
        pkill -f "command_bridge.py serve" 2>/dev/null
        echo "Bridge stopped"
    fi
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "✅ Bridge RUNNING (PID $(cat $PID_FILE))"
        curl -s http://localhost:${WINDI_BRIDGE_PORT:-8097}/health 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "  (health endpoint not responding)"
    else
        echo "❌ Bridge NOT RUNNING"
    fi
}

logs() {
    tail -${2:-50} "$LOG_FILE"
}

case "${1:-start}" in
    start)   start ;;
    stop)    stop ;;
    restart) stop; sleep 1; start ;;
    status)  status ;;
    logs)    logs "$@" ;;
    *)       echo "Usage: $0 {start|stop|restart|status|logs [N]}" ;;
esac

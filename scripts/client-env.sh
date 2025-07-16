export DPS_MODE=client
export DPS_ADDR=http://localhost:5000
export DPS_DEFAULTS=/home/yna/trash/dps/defaults.json
export DPS_LOG_LEVEL=INFO
dps(){
    python3 /home/yna/trash/dps/src/script.py "$@"
}
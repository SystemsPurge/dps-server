export DPS_MODE=client
export DPS_ADDR=http://localhost:5000
export DPS_DEFAULTS=<path to defaults file>
export DPS_LOG_LEVEL=INFO
dps(){
    python3 <path to cli-script.py> "$@"
}
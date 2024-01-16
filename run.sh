#!/bin/bash
echo "© SmartSun EZ-Start"
echo "Bash script written by NTDev-Technology 2024"

STANDARD="SmartSun-V2" # Auto option for CRON
PATH_V1="./SmartSun-V1/main.py"
PATH_V2="./SmartSun-V2"
OPTIONS={"SmartSun versie 1","SmartSun versie 2","quit"}

POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--cron)
            echo "Ez-autostarting $STANDARD - Crashless"
            
            if [ "$STANDARD" == "SmartSun-V2" ]; then
                cd "$PATH_V2"
                gunicorn wsgi:app --bind 0.0.0.0:80 #--workers 1 --timeout 100
            elif [ "$STANDARD" == "SmartSun-V1" ]; then
                python3.11 "$PATH_V1" -c
            else
                echo "Not a valid option for 'Standard'"
            fi
        ;;
    esac
done

if [ "$(id -u)" -ne 0 ];
  then echo "ERROR: Please run as root"
  exit
fi


echo "OPTIONS:
1) Launch SmartSun Versie 1
2) Launch SmartSun Versie 2
3) Update SmartSun
4) Quit"

PS3="SmartSun prompt: "

while true; do
    #echo "$PS3"
    read Opt

    case $Opt in
        "1")
            echo "Starting Version 1 please wait..."
            python3.11 "$PATH_V1" -t;;
        "2")
            echo "Starting Version 2 please wait..."
            cd "$PATH_V2"
            gunicorn wsgi:app --bind 0.0.0.0:80;; #--workers 1 --timeout 100
        "3")
            echo "Updating SmartSun from NTDev-Technology"
            git pull --force origin main
            echo "Exitting SmartSun user prompt..."
            exit 0
            ;;
        "4")
            echo "Exitting SmartSun user prompt..."
            break;;
        *)
            echo "Ooops, that's not an option!"
            echo "Exitting"
            exit 1
            ;;
    esac
done

exit 0

#!/bin/bash
echo "© SmartSun EZ-Start"

STANDARD="SmartSun-V2" # Auto option for CRON
PATH_V1="./SmartSun-V1/main.py"
PATH_V2="./SmartSun-V2"
OPTIONS={"SmartSun versie 1","SmartSun versie 2","quit"}


if [ -z "$TERM" ] && [ -z "$PS1" ]; then
    echo "EZ-AUTOSTARTING $STANDARD"
    
    if [ "$STANDARD" == "SmartSun-V2" ]; then
        cd "$PATH_V2"
        gunicorn -b 0.0.0.0:80 wsgi:app --reload
    elif [ "$STANDARD" == "SmartSun-V1" ]; then
        python3.11 "$PATH_V1" -c
    else
        echo "Not a valid option for 'Standard'"
    fi
fi

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
            gunicorn -b 0.0.0.0:80 wsgi:app --reload;;
        "3")
            echo "Updating SmartSun from NTDev-Technology"
            # Implement logic to auto-update from git
            ;;
        "4")
            echo "Exitting SmartSun user prompt..."
            break;;
        *)
            echo "Ooops, that's not an option!";;
    esac
done

exit 0
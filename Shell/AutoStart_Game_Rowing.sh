#!/bin/bash
echo "AutoStart_Game_Rowing"
cd /home/sood/Desktop/samyang-pop-client
source venv/bin/activate
python3 pop-client.py --tcp --type 3 --countdown-time 30 --score-wait-time 35 --device_id 3
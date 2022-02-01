for RATE_SENDING in $(seq 0.5 0.5 10)
do
    echo -e "\n...SIMULATION STARTS (send_rate=$RATE_SENDING)..."
    python3 playground.py --rate_sending $RATE_SENDING
    echo -e "...SIMULATION ENDS (send_rate=$RATE_SENDING)...\n"
done
echo -e "\n...WHOLE SIMULATION FINISH...\n"
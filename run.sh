#!/bin/bash  

echo 'Starting ticker...'
chmod +x src/tickerapp/ticker_app.py
nohup python3 src/tickerapp/ticker_app.py &


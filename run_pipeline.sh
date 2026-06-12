#!/bin/bash

# 1. Explicitly navigate to your project directory
cd /Users/tomdai/Documents/infra-market-terminal || exit

# 2. Print a timestamp to the hidden log file so you know when it started
echo "--- Automated Run: $(date) ---" >> automation.log

# 3. Run the orchestrator. 
/usr/local/bin/python3 orchestrator.py >> automation.log 2>&1

# 4. Mark the end of the run in the log
echo "Run Complete." >> automation.log
echo "----------------------------------------" >> automation.log
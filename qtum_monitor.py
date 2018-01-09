#!/usr/bin/python

""" 
Simple script to monitor QTUM wallet and notify when blocks are won.
Runs via cron. Ref: https://www.howtoforge.com/a-short-introduction-to-cron-jobs
Example running hourly. Change the first 0 to * if you want updates each minute.
0 * * * * /usr/bin/python /home/pi/qtum_monitor.py

The first time the script runs it saves the current balance and stake data to a file.
On subsequent runs, if 'stake' increases the pings you on Slack
"""
import subprocess
import requests
import json
import os
import sys
import time
import datetime

# Configuration options
NOTIFY_ALWAYS = False # False notifies on wins only, if True also reports general balance updates
DAILY_STATUS_UPDATE = True # Send a daily status update to confirm still running
MONITOR_TEMPERATURE = True # only set true for Raspberry Pi or a system with similar temperature monitoring
TEMPERATURE_WARNING_THRESHOLD = 80.0 # warn if temperature exceeds this threshold in Celsius

# Setup a Slack webhook and then past your URL here
WEBHOOK_URL = 'https://hooks.slack.com/services/YOUR_WEBHOOK_ADDRESS_GOES_HERE'

# You may also need to update this path if you have qtum installed elsewhere
QTUM_PATH = '/usr/local/'
LOG_FILE = QTUM_PATH + 'qtum_monitor.log'

STATE_DATA = {
    'initial_balance': 0.0,
    'balance': 0.0,
    'stake': 0.0,
    'total_balance': 0.0,
    'last_block_time_won': 0, # epoch seconds of last block win
    'date': datetime.date.today().isoformat()
}

if __name__ == '__main__':

    # Method for sending messages to Slack
    def slack_off(message):
        payload = json.dumps({"text": message})
        requests.post(WEBHOOK_URL, data=payload)

    # Get latest wallet info.
    try:
        wallet_info = json.loads(subprocess.check_output([QTUM_PATH + 'bin/qtum-cli', 'getwalletinfo']))
        staking_info = json.loads(subprocess.check_output([QTUM_PATH + 'bin/qtum-cli', 'getstakinginfo']))
    except subprocess.CalledProcessError:
	    slack_off('Error running qtum-cli. Verify settings')
        sys.exit()

    # Pre-checks
    if (not wallet_info['balance']) and (not wallet_info['stake']):
	    slack_off('No QTUM balance.')
        sys.exit()
    if staking_info['errors']:
	    slack_off('QTUM Errors: %s' % (str(staking_info['errors'])))
        sys.exit()
    if wallet_info['unlocked_until'] == 0:
	    slack_off('QTUM Locked - Not Staking')
        sys.exit()
    if staking_info['enabled'] != True:
	    slack_off('QTUM Stacking disabled')
        sys.exit()
    if staking_info['staking'] != True:
	    slack_off('QTUM Not Yet Staking')
        sys.exit()
    if MONITOR_TEMPERATURE:
        temp_str = subprocess.check_output(['/opt/vc/bin/vcgencmd', 'measure_temp'])
        temp = float(temp_str[temp_str.find('=')+1:temp_str.find("'")])
        if temp > TEMPERATURE_WARNING_THRESHOLD:
	        slack_off('QTUM Pi Temperature Warning! %fC above %fC' % (temp, TEMPERATURE_WARNING_THRESHOLD))

    # Prepare relevant state data
    latest_data = STATE_DATA.copy()
    latest_data['balance'] = wallet_info['balance']
    latest_data['stake'] = wallet_info['stake']
    latest_data['total_balance'] = wallet_info['balance'] + wallet_info['stake']
    latest_data['date'] = datetime.date.today().isoformat()

    # Read prior status for comparison, creating log file if none.
    if not os.path.exists(LOG_FILE):
        latest_data['initial_balance'] = wallet_info['balance']
        f = open(LOG_FILE, 'w')
        f.write(json.dumps(latest_data))
        f.close()
	    slack_off('QTUM Monitor initialized')
        sys.exit()

    # Read prior data.
    log_file = open(LOG_FILE, 'r')
    prior_data = json.loads(log_file.read())
    log_file.close()

    # Report on results
    if latest_data['stake'] > prior_data['stake']:
        latest_data['last_block_time_won'] = int(time.time())
	    slack_off('Stake earned! Balance: %d Stake: %d' % (int(latest_data['balance']), int(latest_data['stake'])))
    if NOTIFY_ALWAYS:
	    slack_off('Balance: %d Stake %d' % (int(latest_data['balance']), int(latest_data['stake'])))
    if DAILY_STATUS_UPDATE and (latest_data['date'] != prior_data['date']):
	    slack_off('Daily Update for %s:\nTotal Balance: %d Stake: %d' % (latest_data['date'], int(latest_data['total_balance']), int(latest_data['stake'])))

    # Write latest state to log
    log_file = open(LOG_FILE, 'w')
    log_file.write(json.dumps(latest_data))
    log_file.close()
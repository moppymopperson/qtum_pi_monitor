# QTUM Raspberry Pi Monitor

- This is a fork of [anuzis's work](https://github.com/anuzis/qtum_pi_monitor) that sends messages via Slack instead of email
- Simple script to notify of block wins, monitor temperature, and performs basic sanity checks.
- Easy to review and modify.

# Setup Instructions
- Set WEBHOOK_URL to your address.
- Set QTUM_PATH to where you have QTUM installed.
- Add a cronjob to run the script at your desired frequency. (examples in script)

Easy areas for improvement:
- Report on weekly/monthly/overall growth relative to initial balance
- Report on whether block win timing is lucky/unlucky relative to statistical expectation

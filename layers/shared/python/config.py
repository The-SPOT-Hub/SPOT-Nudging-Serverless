import os

# Slack
spot_channel_id = os.environ.get('SLACK_SPOT_CHANNEL_ID')
slack_bot_token = os.environ.get('SLACK_BOT_TOKEN')
slack_app_id = os.environ.get('SLACK_APP_ID')
get_thread_messages_endpoint = "https://slack.com/api/conversations.replies"
post_message_endpoint = "https://slack.com/api/chat.postMessage"
get_history_endpoint = "https://slack.com/api/conversations.history"
get_permalink_endpoint = "https://slack.com/api/chat.getPermalink"

slack_signing_secret = os.environ.get('SLACK_SIGNING_SECRET')
slack_signing_version = "v0"

# Map courses to Slack channel IDs
course_to_channel = {
    'RB 101-109': os.environ.get('RB_101_CHANNEL_ID'),
    'RB 110-119': os.environ.get('RB_110_CHANNEL_ID'),
    'RB 120-129': os.environ.get('RB_120_CHANNEL_ID'),
    'RB 130-139': os.environ.get('RB_130_CHANNEL_ID'),
    'JS 101-109': os.environ.get('JS_101_CHANNEL_ID'),
    'JS 110-119': os.environ.get('JS_110_CHANNEL_ID'),
    'JS 120-129': os.environ.get('JS_120_CHANNEL_ID'),
    'JS 130-139': os.environ.get('JS_130_CHANNEL_ID'),
    'PY 101-109': os.environ.get('PY_101_CHANNEL_ID'),
    'PY 110-119': os.environ.get('PY_110_CHANNEL_ID'),
    'PY 120-129': os.environ.get('PY_120_CHANNEL_ID'),
    'PY 130-139': os.environ.get('PY_130_CHANNEL_ID'),
    'LS 170-171': os.environ.get('LS_170_CHANNEL_ID'),
    'RB 175': os.environ.get('RB_175_CHANNEL_ID'),
    'JS 175': os.environ.get('JS_175_CHANNEL_ID'),
    'PY 175': os.environ.get('PY_175_CHANNEL_ID'),
    'LS 180-181': os.environ.get('LS_180_CHANNEL_ID'),
    'JS 210-211': os.environ.get('JS_210_CHANNEL_ID'),
    'LS 215-216': os.environ.get('LS_215_CHANNEL_ID'),
    'JS 225-229': os.environ.get('JS_225_CHANNEL_ID'),
    'JS 230-239': os.environ.get('JS_230_CHANNEL_ID'),
    'TS 240-249': os.environ.get('TS_240_CHANNEL_ID'),
    'LS 250-259': os.environ.get('LS_250_CHANNEL_ID')
}

course_channel_post = [
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "Hey everyone! *At least one student has posted their availability for a {course} SPOT session to be scheduled soon.*"
        }
    },
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "You should join them! SPOT sessions are a great way to study and get to know other students."
        }
    },
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "Link to thread: {thread_link}"
        }
    }
]

# DynamoDB
dynamodb_table_name = os.environ.get('DYNAMODB_TABLE_NAME')

# SQS
sqs_queue_url = os.environ.get('SQS_QUEUE_URL')

import copy
import re
import hmac
import hashlib
from datetime import datetime, timezone
import requests
import config

SECONDS_PER_WEEK = 7 * 24 * 60 * 60
REPLAY_ATTACK_THRESHOLD = 60 * 5  # 5 minutes

########## Slack verification ##########

def is_url_verification_challenge(data):
    """Check if request is for Slack URL verification"""
    return data['type'] == 'url_verification'

def is_request_valid(request_body, timestamp, slack_signature):
    """Verify timestamp + signing secret from Slack"""
    current_time = datetime.now(timezone.utc).timestamp()
    if abs(current_time - float(timestamp)) > REPLAY_ATTACK_THRESHOLD:
        return False

    request_body_decoded = request_body.decode('utf-8')
    sig_basestring = config.slack_signing_version + ':' + timestamp + ':' + request_body_decoded
    my_signature = 'v0=' + hmac.new(
        config.slack_signing_secret.encode('utf-8'),
        sig_basestring.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(my_signature, slack_signature)   

########## Slack API helpers ##########

def get_conversation_replies(channel, ts):
    """Get message history for the given thread, based on channel and ts"""
    headers = {
        "Authorization": f"Bearer {config.slack_bot_token}"
    }
    data = {
        "channel": channel,
        "ts": ts
    }
    response = requests.get(
        config.get_thread_messages_endpoint,
        headers=headers,
        params=data,
        timeout=10
    )
    response_json = response.json()
    if not response_json.get('ok'):
        raise RuntimeError(f"Failed: {response_json}")
    return response_json

def get_channel_history(channel_id, min_date_unix):
    """Get messages sent today in the channel. Checks in UTC time"""
    headers = {
        "Authorization": f"Bearer {config.slack_bot_token}"
    }
    data = {
        "channel": channel_id,
        "oldest": min_date_unix
    }
    response = requests.get(
        config.get_history_endpoint,
        headers=headers,
        params=data,
        timeout=10
    )
    response_json = response.json()
    if not response_json.get('ok'):
        raise RuntimeError(f"Failed: {response_json}")
    return response_json['messages']

def get_thread_permalink(channel_id, ts):
    """Get the permalink to the thread to link into course channel post"""
    headers = {
        "Authorization": f"Bearer {config.slack_bot_token}"
    }
    data = {
        "channel": channel_id,
        "message_ts": ts
    }
    response = requests.get(
        config.get_permalink_endpoint,
        headers=headers,
        params=data,
        timeout=10
    )
    response_json = response.json()
    if not response_json.get('ok'):
        raise RuntimeError(f"Failed: {response_json}")
    return response_json['permalink']

def post_to_slack(channel_id, additional_data):
    """Trigger the actual post to Slack"""
    data = {
        "channel": channel_id
    }
    data.update(additional_data)
    headers = {
        "Authorization": f"Bearer {config.slack_bot_token}",
        "Content-Type": "application/json"
    }
    response = requests.post(
        config.post_message_endpoint,
        headers=headers,
        json=data,
        timeout=10
    )
    response_json = response.json()
    if not response_json.get('ok'):
        raise RuntimeError(f"Failed: {response_json}")
    return response_json

########## Parsing JSON helpers ##########

def get_message_text(course_name, thread_link):
    """Generate text for course channel message"""
    blocks = copy.deepcopy(config.course_channel_post)
    for block in blocks:
        block['text']['text'] = block['text']['text'].format(
            course=course_name,
            thread_link=thread_link
        )
    return blocks

def get_course_info(message):
    """Get course info based on parent message"""
    if not message:
        return ""
    text = message.get("text") or ""
    match = re.search(
        r":[^:\s]+:\s+([A-Z]{2}\s+\d+(?:-\d+)?)\b",
        text.strip(),
    )
    return match.group(1) if match else ""

def is_from_spot_channel(event_data):
    """Check if the message was posted in the SPOT channel"""
    return event_data['channel'] == config.spot_channel_id

def is_human_message(event_data):
    """Check if the reply was made by a human, not by a bot"""
    return 'bot_profile' not in event_data

def is_bot_thread(message):
    """Check that parent message was posted by a bot"""
    return message.get('app_id') == config.slack_app_id

def is_current_weekly_thread(message):
    """Check that thread is the latest weekly thread posted by the bot"""
    message_datetime = datetime.fromtimestamp(float(message['thread_ts']))
    time_since_message = datetime.now() - message_datetime
    return time_since_message.total_seconds() < SECONDS_PER_WEEK

def is_thread_reply(event_data):
    """Check if the message is a thread reply"""
    return 'thread_ts' in event_data and event_data['thread_ts'] != event_data['ts']

def get_ls_course_slack_channel_id(course_info):
    """Get the channel ID for the parsed course"""
    return config.course_to_channel.get(course_info)

def has_recent_channel_post(channel_id, parent_ts):
    """Check if there has been a recent post by the bot in the course channel"""
    messages = get_channel_history(channel_id, parent_ts)
    bot_messages = any(
        message for message in messages
        if message.get('app_id') == config.slack_app_id
    )
    return bot_messages

def parse_event_data(data):
    """Main function to parse event data"""
    event_data = data['event']

    if not is_from_spot_channel(event_data):
        return None
    if not is_human_message(event_data):
        return None
    if not is_thread_reply(event_data):
        return None

    channel = event_data['channel']
    ts = event_data['thread_ts']

    thread_history = get_conversation_replies(channel, ts)
    first_message = thread_history['messages'][0]
    if not is_bot_thread(first_message):
        return None

    course_info = get_course_info(first_message)
    if not course_info:
        return None

    if not is_current_weekly_thread(first_message):
        return None

    slack_channel_id = get_ls_course_slack_channel_id(course_info)
    if not slack_channel_id:
        return None

    return {
        "channel": channel,
        "parent_post_ts": ts,
        "course_name": course_info,
        "slack_channel_id": slack_channel_id
    }

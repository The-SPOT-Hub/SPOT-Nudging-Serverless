import json
from helpers import (
    parse_event_data,
    has_recent_channel_post,
    get_thread_permalink,
    post_to_slack,
    get_message_text
)
from database import update_event, is_event_processed

def lambda_handler(event, context):
    for record in event['Records']:
        body = json.loads(record['body'])
        event_id = body['event_id']
        data = body['data']

        # Check in case we have already processed the item
        # (if the item was kept in the queue for some reason)
        if is_event_processed(event_id):
            continue

        info = parse_event_data(data)
        if info is None:
            update_event(event_id, {'status': 'rejected'})
            continue

        update_event(event_id, {'status': 'accepted'})

        channel = info['channel']
        parent_post_ts = info['parent_post_ts']
        course_name = info['course_name']
        course_channel_id = info['slack_channel_id']

        if not has_recent_channel_post(course_channel_id, parent_post_ts):
            permalink = get_thread_permalink(channel, parent_post_ts)
            post_to_slack(
                course_channel_id,
                {"blocks": get_message_text(course_name, permalink)}
            )
            update_event(event_id, {'channel_post_sent': True})

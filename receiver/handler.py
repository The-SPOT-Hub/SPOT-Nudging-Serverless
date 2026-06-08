import json
import boto3
from botocore.exceptions import ClientError
from helpers import is_request_valid, is_url_verification_challenge
from database import insert_new_event, DatabaseError
import config

sqs = boto3.client('sqs')

def lambda_handler(event, context):
    data = json.loads(event['body'])

    # If the request is for URL verification, handle that and return
    if is_url_verification_challenge(data):
        return {
            'statusCode': 200,
            'body': json.dumps({'challenge': data['challenge']})
        }
    
    # Validate request
    if not is_request_valid(
        request_body=event['body'].encode('utf-8'),
        timestamp=event['headers']['X-Slack-Request-Timestamp'],
        slack_signature=event['headers']['x-slack-signature']
    ):
        return {
            'statusCode': 400, 
            'body': 'Request not verified'
        }

    # Otherwise, we're getting a request from an event in our workspace

    # First, add all incoming events to the database
    try:
        event_id = insert_new_event(data)
    except DatabaseError as e:
        return {
            'statusCode': 500,
            'body': str(e)
        }

    # Add to SQS queue
    try:
        sqs.send_message(
            QueueUrl=config.sqs_queue_url,
            MessageBody=json.dumps({'event_id': event_id, 'data': data})
        )
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        return {
            'statusCode': 500,
            'body': f'Error adding to SQS queue: {error_code} - {error_message}'
        }

    return {
        'statusCode': 200,
        'body': 'OK'
    }
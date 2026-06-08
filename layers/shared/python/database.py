import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone
import config

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(config.dynamodb_table_name)

class DatabaseError(Exception):
    """Custom error for database insertion / updates"""
    def __init__(self, message):
        super().__init__(message)

def insert_new_event(payload):
    event_id = payload['event_id']
    now = datetime.now(timezone.utc).isoformat()
    try:
        table.put_item(Item={
            'event_id': event_id,
            'payload': payload,
            'received_at': now,
            'status': 'not_processed',
            'updated_at': now,
            'channel_post_sent': False
        })
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        raise DatabaseError(f'Error inserting event: {error_code} - {error_message}')
    return event_id

def update_event(event_id, fields):
    fields['updated_at'] = datetime.now(timezone.utc).isoformat()
    update_expr = 'SET ' + ', '.join(f'#{k} = :{k}' for k in fields)
    expr_names = {f'#{k}': k for k in fields}
    expr_values = {f':{k}': v for k, v in fields.items()}

    try:
        table.update_item(
            Key={'event_id': event_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values
        )
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        raise DatabaseError(f'Error updating event: {error_code} - {error_message}')

def is_event_processed(event_id):
    try:
        response = table.get_item(
            Key={'event_id': event_id}
        )
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        raise DatabaseError(f'Error looking for event: {error_code} - {error_message}')
        
    item = response.get('Item')
    return (item is not None) and (item['status'] != 'not_processed')

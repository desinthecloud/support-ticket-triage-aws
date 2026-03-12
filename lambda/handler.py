import json
import boto3
import os
from reply_templates import get_reply


ENDPOINT_NAME = os.environ.get('SAGEMAKER_ENDPOINT_NAME', 'support-ticket-triage-2026-03-12-19-09-57-828')


sagemaker_runtime = boto3.client('runtime.sagemaker')


def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        ticket_text = body.get('ticket', '')


        if not ticket_text:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'ticket field is required'})
            }


        # Call SageMaker endpoint
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType='application/json',
            Body=json.dumps([ticket_text])
        )


        result = response['Body'].read().decode().strip()
        category = json.loads(result)[0]
        reply = get_reply(category)

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'ticket': ticket_text,
                'category': category,
                'suggested_reply': reply
            })
        }


    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


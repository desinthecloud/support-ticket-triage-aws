import boto3
import time
import os
import tempfile
from datetime import datetime

sagemaker = boto3.client('sagemaker', region_name=os.environ['AWS_REGION'])
s3 = boto3.client('s3', region_name=os.environ['AWS_REGION'])
sns = boto3.client('sns', region_name=os.environ['AWS_REGION'])

ROLE_ARN = os.environ['SAGEMAKER_ROLE_ARN']
MODEL_BUCKET = os.environ.get('MODEL_BUCKET', 'support-ticket-ml-supporttickets0302')
ENDPOINT_NAME = 'support-ticket-triage-2026-03-12-19-09-57-828'
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
IMAGE_URI = '683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:1.2-1-cpu-py3'


def send_alert(subject, message):
    sns.publish(TopicArn=SNS_TOPIC_ARN, Subject=subject, Message=message)


def deploy():
    with open('validated_artifact_uri.txt', 'r') as f:
        artifact_uri = f.read().strip()

    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    model_name = f'support-ticket-model-{timestamp}'
    config_name = f'support-ticket-config-{timestamp}'

    print(f'Creating model: {model_name}')
    sagemaker.create_model(
        ModelName=model_name,
        PrimaryContainer={
            'Image': IMAGE_URI,
            'ModelDataUrl': artifact_uri
        },
        ExecutionRoleArn=ROLE_ARN
    )

    print(f'Creating endpoint config: {config_name}')
    sagemaker.create_endpoint_config(
        EndpointConfigName=config_name,
        ProductionVariants=[{
            'VariantName': 'AllTraffic',
            'ModelName': model_name,
            'InitialInstanceCount': 1,
            'InstanceType': 'ml.t2.medium',
            'InitialVariantWeight': 1
        }]
    )

    try:
        sagemaker.describe_endpoint(EndpointName=ENDPOINT_NAME)
        print(f'Updating endpoint: {ENDPOINT_NAME}')
        sagemaker.update_endpoint(
            EndpointName=ENDPOINT_NAME,
            EndpointConfigName=config_name
        )
    except Exception:
        print(f'Creating endpoint: {ENDPOINT_NAME}')
        sagemaker.create_endpoint(
            EndpointName=ENDPOINT_NAME,
            EndpointConfigName=config_name
        )

    while True:
        response = sagemaker.describe_endpoint(EndpointName=ENDPOINT_NAME)
        status = response['EndpointStatus']
        print(f'Endpoint status: {status}')

        if status == 'InService':
            break
        elif status in ['Failed', 'OutOfService']:
            send_alert(
                '[MLOps] FAILED: Endpoint Update',
                f'Endpoint update failed. Status: {status}'
            )
            raise Exception(f'Endpoint update failed: {status}')
        time.sleep(30)

    with tempfile.TemporaryDirectory() as tmpdir:
        local = f'{tmpdir}/baseline.txt'
        with open(local, 'w') as f:
            f.write(artifact_uri)
        s3.upload_file(local, MODEL_BUCKET, 'models/baseline_artifact_uri.txt')

    send_alert(
        '[MLOps] Deployment Complete',
        f'New model deployed successfully.\nEndpoint: {ENDPOINT_NAME}\nArtifact: {artifact_uri}'
    )
    print('Deployment complete.')


if __name__ == '__main__':
    deploy()

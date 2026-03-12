import boto3
import json
import os
import time
from datetime import datetime

sagemaker = boto3.client('sagemaker', region_name=os.environ['AWS_REGION'])
sns = boto3.client('sns', region_name=os.environ['AWS_REGION'])

ROLE_ARN = os.environ['SAGEMAKER_ROLE_ARN']
TRAINING_BUCKET = os.environ.get('TRAINING_BUCKET', 'support-ticket-training-data')
MODEL_BUCKET = os.environ.get('MODEL_BUCKET', 'support-ticket-models')
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
IMAGE_URI = '683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:1.2-1-cpu-py3'


def send_alert(subject, message):
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=subject,
        Message=message
    )


def run_training_job():
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    job_name = f'support-ticket-retrain-{timestamp}'

    send_alert(
        subject='[MLOps] Pipeline Started: Retraining',
        message=f'Retraining job started.\nJob: {job_name}\nData: s3://{TRAINING_BUCKET}/data/'
    )

    sagemaker.create_training_job(
        TrainingJobName=job_name,
        AlgorithmSpecification={
            'TrainingImage': IMAGE_URI,
            'TrainingInputMode': 'File'
        },
        RoleArn=ROLE_ARN,
        InputDataConfig=[{
            'ChannelName': 'training',
            'DataSource': {
                'S3DataSource': {
                    'S3DataType': 'S3Prefix',
                    'S3Uri': f's3://{TRAINING_BUCKET}/data/',
                    'S3DataDistributionType': 'FullyReplicated'
                }
            },
            'ContentType': 'text/csv'
        }],
        OutputDataConfig={
            'S3OutputPath': f's3://{MODEL_BUCKET}/models/'
        },
        ResourceConfig={
            'InstanceType': 'ml.m5.large',
            'InstanceCount': 1,
            'VolumeSizeInGB': 5
        },
        StoppingCondition={'MaxRuntimeInSeconds': 3600},
        HyperParameters={
            'sagemaker_program': 'train.py',
            'sagemaker_submit_directory': f's3://{TRAINING_BUCKET}/source/sourcedir.tar.gz'
        }
    )

    print(f'Training job started: {job_name}')

    # Wait for job to complete
    while True:
        response = sagemaker.describe_training_job(TrainingJobName=job_name)
        status = response['TrainingJobStatus']
        print(f'Job status: {status}')

        if status == 'Completed':
            model_artifact = response['ModelArtifacts']['S3ModelArtifacts']
            print(f'Model artifact: {model_artifact}')
            # Write to file for next pipeline step
            with open('model_artifact_uri.txt', 'w') as f:
                f.write(model_artifact)
            return model_artifact
        elif status in ['Failed', 'Stopped']:
            reason = response.get('FailureReason', 'Unknown')
            send_alert(
                subject='[MLOps] FAILED: Retraining Job',
                message=f'Training job failed.\nJob: {job_name}\nReason: {reason}'
            )
            raise Exception(f'Training job failed: {reason}')

        time.sleep(60)


if __name__ == '__main__':
    run_training_job()


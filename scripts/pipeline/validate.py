import boto3
import joblib
import json
import os
import tarfile
import tempfile
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

s3 = boto3.client('s3', region_name=os.environ['AWS_REGION'])
sns = boto3.client('sns', region_name=os.environ['AWS_REGION'])

SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
TRAINING_BUCKET = os.environ.get('TRAINING_BUCKET', 'support-ticket-ml-supporttickets0302')
MODEL_BUCKET = os.environ.get('MODEL_BUCKET', 'support-ticket-ml-supporttickets0302')

ACCURACY_THRESHOLD = 0.80   # New model must hit at least 80% accuracy
F1_THRESHOLD = 0.78         # New model must hit at least 0.78 weighted F1
IMPROVEMENT_MARGIN = 0.01   # New model must beat baseline by at least 1%


def send_alert(subject, message):
    sns.publish(TopicArn=SNS_TOPIC_ARN, Subject=subject, Message=message)

def download_model(artifact_uri):
    bucket = artifact_uri.split('/')[2]
    key = '/'.join(artifact_uri.split('/')[3:])

    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = f'{tmpdir}/model.tar.gz'
        s3.download_file(bucket, key, local_path)

        with tarfile.open(local_path, 'r:gz') as tar:
            tar.extractall(tmpdir)

        model_path = f'{tmpdir}/model.joblib'
        return joblib.load(model_path)

def load_test_data():
    """Load held-out test set from S3."""
    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = '/tmp/tickets.csv'
        s3.download_file(TRAINING_BUCKET, 'data/tickets.csv', local_path)
        df = pd.read_csv(local_path)
        return df['text'].tolist(), df['category'].tolist()


def evaluate_model(model, texts, labels):
    predictions = model.predict(texts)
    accuracy = accuracy_score(labels, predictions)
    f1 = f1_score(labels, predictions, average='weighted')
    return accuracy, f1


def validate():
    # Read new model artifact URI from retrain step
    with open('model_artifact_uri.txt', 'r') as f:
        new_artifact_uri = f.read().strip()

    # Read baseline artifact URI (stored after each successful deploy)
    try:
        baseline_key = 'models/baseline_artifact_uri.txt'
        with tempfile.TemporaryDirectory() as tmpdir:
            local = f'{tmpdir}/baseline.txt'
            s3.download_file(MODEL_BUCKET, baseline_key, local)
            with open(local) as f:
                baseline_artifact_uri = f.read().strip()
        has_baseline = True
    except Exception:
        print('No baseline found. Treating this as first deployment.')
        has_baseline = False

    texts, labels = load_test_data()
    new_model = download_model(new_artifact_uri)
    new_accuracy, new_f1 = evaluate_model(new_model, texts, labels)

    print(f'New model  accuracy={new_accuracy:.4f}  f1={new_f1:.4f}')

    # Check absolute thresholds
    if new_accuracy < ACCURACY_THRESHOLD or new_f1 < F1_THRESHOLD:
        message = (
            f'Validation FAILED. Model did not meet minimum thresholds.\n'
            f'Accuracy: {new_accuracy:.4f} (min {ACCURACY_THRESHOLD})\n'
            f'F1 Score: {new_f1:.4f} (min {F1_THRESHOLD})'
        )
        send_alert('[MLOps] BLOCKED: Model Below Threshold', message)
        raise Exception('Model did not meet minimum quality thresholds')

    # Compare against baseline if one exists
    if has_baseline:
        baseline_model = download_model(baseline_artifact_uri)
        base_accuracy, base_f1 = evaluate_model(baseline_model, texts, labels)
        print(f'Baseline   accuracy={base_accuracy:.4f}  f1={base_f1:.4f}')

        if new_accuracy < base_accuracy - IMPROVEMENT_MARGIN:
            message = (
                f'Validation FAILED. New model is worse than baseline.\n'
                f'New accuracy: {new_accuracy:.4f}\n'
                f'Baseline accuracy: {base_accuracy:.4f}'
            )
            send_alert('[MLOps] BLOCKED: New Model Worse Than Baseline', message)
            raise Exception('New model did not improve over baseline')

    # Validation passed
    message = (
        f'Validation PASSED. Proceeding to deployment.\n'
        f'New model accuracy: {new_accuracy:.4f}\n'
        f'New model F1: {new_f1:.4f}'
    )
    send_alert('[MLOps] Validation Passed: Deploying New Model', message)
    print('Validation passed. Writing artifact URI for deploy step.')

    # Pass artifact URI to deploy step
    with open('validated_artifact_uri.txt', 'w') as f:
        f.write(new_artifact_uri)


if __name__ == '__main__':
    validate()


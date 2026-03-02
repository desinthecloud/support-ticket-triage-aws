import sagemaker
from sagemaker.sklearn.estimator import SKLearn


# Replace these values with your Terraform outputs
BUCKET_NAME = 'support-ticket-ml-supporttickets0302'
ROLE_ARN    = 'arn:aws:iam::140324736937:role/support-ticket-ml-sagemaker-role'


session = sagemaker.Session()


# Define the estimator
estimator = SKLearn(
    entry_point='train.py',
    source_dir='training',
    role=ROLE_ARN,
    framework_version='1.2-1',
    instance_type='ml.m5.large',
    instance_count=1,
    base_job_name='support-ticket-triage',
    output_path=f's3://{BUCKET_NAME}/model-artifacts/',
    sagemaker_session=session
)


# Point to the training data in S3
training_input = f's3://{BUCKET_NAME}/data/'


# Launch the training job
estimator.fit({'train': training_input})


print('Training complete')
print(f'Model artifact: {estimator.model_data}')

# Deploy to a real-time endpoint
predictor = estimator.deploy(
    initial_instance_count=1,
    instance_type='ml.t2.medium'  # Cheapest instance for testing
)


print(f'Endpoint name: {predictor.endpoint_name}')
print('Save this endpoint name. You will use it in Lambda.')


# Test the endpoint directly
result = predictor.predict(['I was charged twice for my subscription'])
print(result)  # Should return ['billing']


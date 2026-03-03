import sagemaker
from sagemaker.sklearn.estimator import SKLearn

BUCKET_NAME = 'support-ticket-ml-supporttickets0302'
ROLE_ARN    = 'arn:aws:iam::140324736937:role/support-ticket-ml-sagemaker-role'
MODEL_URI   = 's3://support-ticket-ml-supporttickets0302/model-artifacts/support-ticket-triage-2026-03-02-22-50-58-908/output/model.tar.gz'

session = sagemaker.Session()

model = sagemaker.sklearn.model.SKLearnModel(
    model_data=MODEL_URI,
    role=ROLE_ARN,
    framework_version='1.2-1',
    entry_point='train.py',
    source_dir='training'
)

predictor = model.deploy(
    initial_instance_count=1,
    instance_type='ml.t2.medium'
)

print(f'Endpoint name: {predictor.endpoint_name}')

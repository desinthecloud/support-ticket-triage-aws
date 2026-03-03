# Support Ticket Triage and Reply Assist

A machine learning system that classifies incoming support tickets by category and returns a suggested reply template. Built end to end on AWS using SageMaker, Lambda, API Gateway, and Terraform.

---

## What It Does

Send a support ticket as plain text to a REST API. Get back a predicted category and a pre-written reply draft.

```bash
curl -X POST https://your-api-endpoint.execute-api.us-east-1.amazonaws.com \
  -H 'Content-Type: application/json' \
  -d '{"ticket": "I was charged twice this month and need a refund"}'
```

```json
{
  "ticket": "I was charged twice this month and need a refund",
  "category": "billing",
  "suggested_reply": "Thank you for reaching out about your billing concern. I have flagged your account for our billing team and they will review the charge within 1 to 2 business days. You will receive a follow-up email with the outcome."
}
```

**Supported categories:** billing, technical, account, shipping, general

---

## Architecture

```
Client → API Gateway → Lambda → SageMaker Endpoint → Reply Templates → JSON Response
```

- **SageMaker** trains and hosts the classification model
- **Terraform** provisions all AWS infrastructure as code
- **Lambda** handles inference routing and reply template lookup
- **API Gateway** exposes the public HTTPS endpoint
- **S3** stores training data and model artifacts

> Architecture diagram built with [Cloudviz.io](https://cloudviz.io)

---

## Model

The classifier uses a scikit-learn Pipeline with two steps:

- **TF-IDF Vectorizer** converts ticket text into weighted word vectors using unigrams and bigrams
- **Logistic Regression** classifies the vector into one of five support categories

Accuracy on the test set: above 90%.

A classical text classifier was chosen over a language model deliberately. For a five-category classification problem with short, clean tickets, TF-IDF and Logistic Regression delivers high accuracy at low latency and near-zero cost per inference.

---

## Project Structure

```
support-ticket-ml/
  terraform/
    main.tf               # S3 bucket and SageMaker IAM role
    variables.tf
    outputs.tf
  data/
    generate_data.py      # Synthetic ticket dataset generator
    tickets.csv           # 140 labeled training examples
  training/
    train.py              # scikit-learn pipeline with SageMaker inference handlers
    run_training_job.py   # Launches SageMaker training job
    deploy_endpoint.py    # Deploys trained model to SageMaker endpoint
  lambda/
    handler.py            # Lambda function and SageMaker invocation logic
    reply_templates.py    # Category to reply template mapping
  README.md
```

---

## Prerequisites

- AWS account with admin IAM access
- AWS CLI installed and configured
- Terraform installed
- Python 3.9 or higher
- Required Python packages:

```bash
pip install pandas scikit-learn boto3 sagemaker joblib
```

---

## Deployment

**1. Clone the repo**

```bash
git clone https://github.com/desinthecloud/support-ticket-triage-aws.git
cd support-ticket-triage-aws
```

**2. Generate training data**

```bash
python3 data/generate_data.py
```

**3. Deploy infrastructure with Terraform**

```bash
cd terraform
terraform init
terraform apply -var='bucket_suffix=yourname123'
```

Save the `bucket_name` and `sagemaker_role_arn` outputs.

**4. Upload training data to S3**

```bash
cd ..
aws s3 cp data/tickets.csv s3://YOUR_BUCKET_NAME/data/tickets.csv
```

**5. Train and deploy the model**

Update `BUCKET_NAME` and `ROLE_ARN` in `training/run_training_job.py` with your Terraform outputs, then run:

```bash
python3 training/run_training_job.py
```

Save the endpoint name printed at the end.

**6. Deploy Lambda**

```bash
cd lambda
zip -r function.zip handler.py reply_templates.py

aws lambda create-function \
  --function-name support-ticket-triage \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/support-ticket-lambda-role \
  --handler handler.lambda_handler \
  --zip-file fileb://function.zip \
  --environment Variables={SAGEMAKER_ENDPOINT_NAME=YOUR_ENDPOINT_NAME} \
  --timeout 30
```

**7. Create API Gateway**

```bash
aws apigatewayv2 create-api \
  --name support-ticket-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:support-ticket-triage
```

---

## Testing

```bash
curl -X POST YOUR_API_ENDPOINT \
  -H 'Content-Type: application/json' \
  -d '{"ticket": "The app crashes every time I open it"}'
```

---

## Cleanup

Delete resources to avoid ongoing AWS charges. The SageMaker endpoint is the only meaningful cost.

```bash
# Delete the SageMaker endpoint
aws sagemaker delete-endpoint --endpoint-name YOUR_ENDPOINT_NAME

# Delete the Lambda function
aws lambda delete-function --function-name support-ticket-triage

# Destroy Terraform resources
cd terraform
aws s3 rm s3://YOUR_BUCKET_NAME --recursive
terraform destroy -var='bucket_suffix=yourname123'
```

---

## Cost

| Scenario | Monthly Cost |
|---|---|
| Portfolio project (test and delete) | Under $5 |
| 250-person company, business hours only | ~$15 |
| 250-person company, 24/7 | ~$47 |

The SageMaker endpoint is the only significant cost driver. Delete it between sessions if you are using this for learning or testing.

---

## Related

- Medium article: [Why I Used scikit-learn Instead of a Language Model to Build a Support Ticket Classifier on AWS](https://medium.com/@djweston38/why-i-used-scikit-learn-instead-of-a-language-model-to-build-a-support-ticket-classifier-on-aws-af28f4d23e73)
- Author: [Des in the Cloud](https://github.com/desinthecloud)


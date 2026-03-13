# Support Ticket Triage and Reply Assist

An end-to-end ML system built across two projects. Project 1 trains and deploys a classifier that triages support tickets and returns a suggested reply. Project 2 automates the full model lifecycle so the system retrains and redeploys itself when new data arrives.

---

## Projects

### Project 1: Classifier and API

A scikit-learn text classifier deployed on AWS as a REST API. Send a ticket, get back a predicted category and a pre-written reply draft.

**Stack:** scikit-learn, SageMaker, Lambda, API Gateway, Terraform, S3

**Tag:** [v1.0.0](https://github.com/desinthecloud/support-ticket-triage-aws/releases/tag/v1.0.0)

**Article:** [Why I Used scikit-learn Instead of a Language Model to Build a Support Ticket Classifier on AWS](https://medium.com/@djweston38/why-i-used-scikit-learn-instead-of-a-language-model-to-build-a-support-ticket-classifier-on-aws-af28f4d23e73)

---

### Project 2: MLOps CI/CD Pipeline

Automated retraining pipeline built on top of Project 1. Upload new ticket data to S3 and the pipeline handles everything else: retrain, validate against accuracy and F1 thresholds, compare to baseline, deploy only if the model improves. Email alerts at every stage.

**Stack:** GitHub Actions, SageMaker, EventBridge, Lambda, SNS, Secrets Manager, Terraform

**Article:** [My Support Ticket Classifier Was Already Stale the Day I Deployed It](https://medium.com/@djweston38/c4316b4e36f8)

---

## How It Works

### Project 1 Flow

```
Client request
  → API Gateway
  → Lambda
  → SageMaker endpoint
  → Reply template lookup
  → JSON response
```

### Project 2 Flow

```
New CSV uploaded to S3
  → EventBridge detects upload
  → Lambda triggers GitHub Actions
  → Test → Retrain → Validate → Deploy
  → SNS email alerts at each stage
```

---

## Example Request

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

## Model

The classifier uses a scikit-learn pipeline with two steps:

- **TF-IDF Vectorizer** converts ticket text into weighted word vectors using unigrams and bigrams
- **Logistic Regression** classifies the vector into one of five support categories

Accuracy on the test set: above 90%.

A classical text classifier was chosen over a language model deliberately. For a five-category classification problem with short, clean tickets, TF-IDF and Logistic Regression delivers high accuracy at low latency and near-zero cost per inference.

---

## Validation Gate

The Project 2 pipeline does not deploy blindly. Before any deployment, the new model must pass two checks:

1. **Absolute thresholds:** accuracy above 80% and weighted F1 above 0.78
2. **Baseline comparison:** new model must not fall more than 1% below the accuracy of the currently deployed model

If either check fails, the pipeline stops and sends an alert. The existing endpoint stays up.

---

## Project Structure

```
support-ticket-triage-aws/
├── .github/
│   └── workflows/
│       └── ml-pipeline.yml        # Project 2: GitHub Actions workflow
├── data/
│   └── generate_data.py           # Synthetic ticket dataset generator
├── lambda/
│   ├── handler.py                 # Project 1: inference routing
│   └── reply_templates.py         # Category to reply template mapping
├── scripts/
│   ├── pipeline/
│   │   ├── retrain.py             # Project 2: SageMaker training job
│   │   ├── validate.py            # Project 2: model validation
│   │   └── deploy.py              # Project 2: endpoint update
│   └── trigger/
│       └── github_dispatch.py     # Project 2: Lambda dispatch handler
├── terraform/
│   ├── main.tf                    # S3, IAM, SageMaker, API Gateway
│   ├── variables.tf
│   ├── outputs.tf
│   ├── sns.tf                     # Project 2: SNS alerts
│   └── lambda_trigger.tf          # Project 2: EventBridge + Lambda trigger
├── tests/
│   └── test_model_validation.py   # Project 2: validation unit tests
├── training/
│   ├── train.py                   # scikit-learn pipeline + SageMaker handlers
│   ├── run_training_job.py        # Launches SageMaker training job
│   └── deploy_endpoint.py         # Deploys trained model to endpoint
├── requirements.txt
└── README.md
```

---

## Prerequisites

- AWS account with admin IAM access
- AWS CLI installed and configured
- Terraform installed
- Python 3.9 or higher

```bash
pip install -r requirements.txt
```

---

## Project 1 Deployment

**1. Clone the repo**

```bash
git clone https://github.com/desinthecloud/support-ticket-triage-aws.git
cd support-ticket-triage-aws
```

**2. Generate training data**

```bash
python3 data/generate_data.py
```

**3. Deploy infrastructure**

```bash
cd terraform
terraform init
terraform apply -var='bucket_suffix=yourname123'
```

Save the `bucket_name` and `sagemaker_role_arn` outputs.

**4. Upload training data**

```bash
aws s3 cp data/tickets.csv s3://YOUR_BUCKET_NAME/data/tickets.csv
```

**5. Train and deploy the model**

Update `BUCKET_NAME` and `ROLE_ARN` in `training/run_training_job.py`, then run:

```bash
python3 training/run_training_job.py
```

**6. Deploy Lambda and API Gateway**

See the deployment steps in the [Project 1 Medium article](https://medium.com/@djweston38/why-i-used-scikit-learn-instead-of-a-language-model-to-build-a-support-ticket-classifier-on-aws-af28f4d23e73) for the full Lambda and API Gateway setup.

---

## Project 2 Setup

Project 2 requires Project 1 to be fully deployed first.

**1. Add GitHub Secrets**

In your repo, go to Settings > Secrets and variables > Actions and add:

| Secret | Value |
|---|---|
| AWS_ACCESS_KEY_ID | Your AWS access key |
| AWS_SECRET_ACCESS_KEY | Your AWS secret key |
| AWS_REGION | us-east-1 |
| SAGEMAKER_ROLE_ARN | IAM role ARN from Project 1 |
| SNS_TOPIC_ARN | ARN output from terraform apply |

**2. Deploy Project 2 infrastructure**

```bash
cd terraform
terraform apply -var='alert_email=your@email.com' -var='bucket_suffix=yourname123'
```

Confirm the AWS subscription email to activate SNS alerts.

**3. Store GitHub token in Secrets Manager**

```bash
aws secretsmanager create-secret \
  --name github-actions-token \
  --secret-string '{"token":"your_github_pat_here"}'
```

**4. Test the pipeline**

Upload new data to trigger the full automated run:

```bash
aws s3 cp data/tickets.csv s3://YOUR_BUCKET_NAME/data/tickets.csv
```

Watch GitHub Actions for the automatic workflow trigger.

---

## Testing

```bash
curl -X POST YOUR_API_ENDPOINT \
  -H 'Content-Type: application/json' \
  -d '{"ticket": "The app crashes every time I open it"}'
```

---

## Cleanup

```bash
# Delete SageMaker endpoint
aws sagemaker delete-endpoint --endpoint-name YOUR_ENDPOINT_NAME

# Delete Lambda trigger function
aws lambda delete-function --function-name support-ticket-github-dispatch

# Empty and destroy Terraform resources
aws s3 rm s3://YOUR_BUCKET_NAME --recursive
cd terraform
terraform destroy -var='alert_email=your@email.com' -var='bucket_suffix=yourname123'
```

Note: if Terraform destroy fails on the S3 bucket, delete object versions manually first using `aws s3api delete-objects`.

---

## Cost

| Resource | Portfolio cost | Production estimate |
|---|---|---|
| SageMaker training (ml.m5.large) | ~$0.12 per run | ~$0.12 per run |
| SageMaker endpoint (ml.t2.medium) | ~$0.065/hr | ~$47/month |
| Lambda invocations | Effectively free | Effectively free |
| EventBridge | Effectively free | Effectively free |
| SNS emails | Effectively free | Effectively free |

Delete the endpoint between sessions to avoid ongoing charges.

---

## Related

- **Project 1 article:** [Why I Used scikit-learn Instead of a Language Model to Build a Support Ticket Classifier on AWS](https://medium.com/@djweston38/why-i-used-scikit-learn-instead-of-a-language-model-to-build-a-support-ticket-classifier-on-aws-af28f4d23e73)
- **Project 2 article:** [My Support Ticket Classifier Was Already Stale the Day I Deployed It](https://medium.com/@djweston38/c4316b4e36f8)
- **Author:** [Des in the Cloud](https://github.com/desinthecloud)

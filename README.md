# S3 Bucket Size Monitoring

Serverless application to track S3 bucket size and visualize it.

## Components
- **Size Tracking Lambda** – triggered by S3 events, stores bucket size in DynamoDB.
- **Driver Lambda** – simulates bucket operations.
- **Plotting Lambda** – reads data from DynamoDB and generates a plot.

## Services Used
AWS Lambda, S3, DynamoDB, API Gateway, AWS CDK.

## Deploy
```bash
cdk deploy --all
```
## Deploy
```bash
cdk destroy --all
```
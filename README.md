# JIRA Issue Automation for AWS Health Event
This is a Lambda Function to trigger Jira Issue Creation by AWS Health Event.

##  How to Use
To use this, please follow this steps
- Clone the repo
- cd aws-maintenance-lambda
- install modules using pip to project folder, pip install -t ./
- zip the contents of aws-maintenance-lambda
- upload to AWS Lambda

## Lambda Service Role
This function needs following policies:
- KMS decrypt and encrypt (since I use Basic Auth for Jira Authentication)
- EC2 describe instances and describe instances status
- Basic Lambda Execution

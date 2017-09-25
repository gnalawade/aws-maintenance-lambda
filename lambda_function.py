from __future__ import print_function

import os
import logging
from base64 import b64decode
import boto3
from jira import JIRA

# aws lambda environment variables encryption using kms
ENCRYPTED = os.environ['JIRA_PASS']
DECRYPTED = boto3.client('kms').decrypt(
    CiphertextBlob=b64decode(ENCRYPTED))['Plaintext']

# setup logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info('Event: ' + str(event))

    instance_ids = event['resources']
    start_time = event['detail']['startTime']
    event_description = event['detail']['eventDescription'][0]['latestDescription']

    instance_status = boto3.client('ec2').describe_instance_status(
        InstanceIds=instance_ids)
    events = instance_status['InstanceStatuses'][0]['Events'][0]

    # jira authentication
    jira = JIRA(
        os.environ['JIRA_URL'],
        basic_auth=(os.environ['JIRA_USER'], DECRYPTED))

    # templating jira description
    description = """
    h1.Team Notes
    - scheduled for *%s* before %s

    h1.Request Details
    h2.Background
    {quote}
    %s
    {quote}
    h2.Purpose
    To minimize disruption of service.

    h2.Impact
    Instance will be down for approximately 5-10 minutes.
    """ % (
        events['Code'],
        start_time,
        event_description
    )

    # jira issue structure
    issue_data = {
        'summary': 'Scheduled AWS Maintenance for ' + ''.join(instance_ids),
        'project': {'key': os.environ['JIRA_PROJECT']},
        'description': description,
        'issuetype': {'id': os.environ['JIRA_ISSUETYPE_ID']},
        'priority': {'name': 'High'},
        'labels': ['scheduled-maintenance'],
    }

    # logging issue data and create issue from jira client
    logger.info(issue_data)
    jira.create_issue(issue_data)

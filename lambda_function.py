from __future__ import print_function

import os
import logging
import pprint
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
    """
    main lambda function for handling events of AWS instance health
    """
    logger.info('Event: ' + str(event))

    instance_ids = event['resources']
    event_description = event['detail']['eventDescription'][0]['latestDescription']
    event_type_code = event['detail']['eventTypeCode']
    if event_type_code == 'AWS_EC2_PERSISTENT_INSTANCE_RETIREMENT_SCHEDULED':
        event_type_code = 'retirement'
    else:
        event_type_code = 'maintenance'

    # jira authentication
    jira = JIRA(
        os.environ['JIRA_URL'],
        basic_auth=(os.environ['JIRA_USER'], DECRYPTED))

    # templating jira description
    description = """
    h1. Team Notes
    h2. Blockers
    - (-) approval from service team to execute preventive stop-start procedure

    h1. Request Details
    h2. Background
    We have received the following alert from AWS:
    {quote}
    %s
    {quote}

    h2. Purpose
    To minimize disruption to the service, we should stop and start this instance as soon as possible.
    Stopping and starting the instance should move it to different underlying hardware and clear AWS scheduled retirement event.

    h2. Impact
    AWS notice alerts of hardware degradation, and this instance may already be impacted.
    If you do not respond to this issue your instance will be restarted or terminated in accordance with AWS retirement schedule.

    If you chose to stop-start the instance ahead of schedule, the instance will be down for approximately 5-10 minutes, but in some cases might take up to 1 hour due to hardware degradation.
    After restart service should resume as normal (unless your application does not start automatically after reboot).
    """ % (
        event_description
    )

    # jira issue structure
    issue_data = {
        'summary': 'stop-start ' + ''.join(instance_ids) + ' for scheduled ' + event_type_code,
        'project': {
            'key': os.environ['JIRA_PROJECT']},
        'description': description,
        'issuetype': {
            'id': os.environ['JIRA_ISSUETYPE_ID']},
        'priority': {
            'name': 'High'},
        'labels': [
            'scheduled-' + event_type_code],
    }

    # logging issue data and create issue from jira client
    logger.info(pprint.pformat(issue_data))
    jira.create_issue(issue_data)

from __future__ import print_function

import boto3
import logging
import os

from base64 import b64decode

ENCRYPTED = os.environ['JIRA_PASS']
DECRYPTED = boto3.client('kms').decrypt(
    CiphertextBlob=b64decode(ENCRYPTED))['Plaintext']

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info('Event: ' + str(event))

    instance_name = ''
    instance_cluster = ''
    instance_id = event['detail']['affectedEntities'][0]['entityValue']
    start_time = event['detail']['startTime']
    res = boto3.resource('ec2').Instance(instance_id)
    for tags in res.tags:
        if tags['Key'] == 'Name':
            instance_name = tags['Value']
        if tags['Key'] == 'Cluster' and tags['Value'] != '':
            instance_cluster = tags['Value']
        else:
            instance_cluster = instance_name
    events = boto3.client('ec2').describe_instance_status(
        InstanceIds=[instance_id])
    events = events['InstanceStatuses'][0]['Events'][0]

    # jira = JIRA(
    #    os.environ['JIRA_URL'],
    #    basic_auth=(os.environ['JIRA_USER'],DECRYPTED))

    description = """
    h2.Notes
    Scheduled for *%s* (%s) at %s

    h2.Background
    We got this email from AWS:
    {quote}
    %s
    {quote}
    h2.Request
    - stop-start instance before AWS maintenance window
    """ % (
        events['Code'],
        events['Description'],
        start_time,
        event['detail']['eventDescription'][0]['latestDescription']
    )

    issue_data = {
        'project': {'key': os.environ['JIRA_PROJECT']},
        'summary': 'AWS Maintenance (' + instance_name + ')',
        'description': description,
        'issuetype': {'id': os.environ['JIRA_ISSUETYPE_ID']},
        'priority': {'name': 'Medium'},
        'labels': [instance_cluster, 'scheduled-maintenance'],
    }

    logger.info(issue_data)
    # jira.create_issue(issue_data)

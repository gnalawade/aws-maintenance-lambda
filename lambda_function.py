from __future__ import print_function

import os
import logging
import pprint
from base64 import b64decode
import boto3
from jira import JIRA
import jinja2

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

    template = jinja2.Environment(
        loader=jinja2.FileSystemLoader("./")
    ).get_template("description.j2")
    description = template.render(
        event_description=event_description
    )

    # jira issue structure
    issue_data = {
        'summary': 'Stop-start ' + ''.join(instance_ids) + ' for scheduled ' + event_type_code,
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

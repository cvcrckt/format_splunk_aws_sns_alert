import boto3
import json
import re
import os
import pprint

# Called if USE_PPRINT is 0
# Return a (sorta-)pretty-printed str version of a dict with keys sorted.
# Exclude empty elements from the result if EXCLUDE_EMPTY_FIELDS is non-zero.
# Lists and their elements will be printed as-is--
# this function does not currently walk them.
# Set USE_PPRINT to 1 to avoid this function and use pprint to recursively walk
# the whole dict, all lists, their elements, etc.
# For simple alerts with fewer layers (i.e. without $result._raw$),
# this function produces nicer looking results.
def format_dict(d, exclude_empty=True, level=0):
    result = ''
    for k in sorted(d.keys()):
        if exclude_empty == True and (d[k] == '' or d[k] == None):
            next
        elif type(d[k]) == dict:
            result += "\t" * level + k + ":\n" + format_dict(d[k], level=level+1)
        else:
            result += "\t" * level + k + ": " + str(d[k]) + "\n"
    return result

# main handler
def lambda_handler(event, context):
    print("loading format-splunk-aws-sns-alert handler")
    sns = boto3.client(service_name="sns")

    try:
        output_topic_arn = os.environ['OUTPUT_TOPIC_ARN']
        if os.environ['EXCLUDE_EMPTY_FIELDS'] == '0':
            exclude_empty_fields = False
        else:
            exclude_empty_fields = True
    except KeyError:
        print("exiting with error: environment variables OUTPUT_TOPIC_ARN and EXCLUDE_EMPTY_FIELDS are required")
        exit(1)

    try:
        if os.environ['USE_PPRINT'] == '0':
            use_pprint = False
        else:
            use_pprint = True
    except KeyError:
            print('USE_PPRINT not provided; defaulting to False')
            use_pprint = False

    for record in event['Records']:
        subject = record['Sns']['Subject']
        inbound_raw_json = record['Sns']['Message']

        # If $result._raw$ is included in the Splunk Alert Trigger Action,
        # it'll be quoted/escaped JSON. We will do some unescaping.
        # Otherwise, json.loads() will choke. THIS IS A HACK--IF YOU HAVE
        # ESCAPED QUOTES ELSEWHERE IN YOUR ALERT BODY THEY WILL BE UNESCAPED.
        inbound_raw_json = re.sub(r'\\([\'"])', r'\1', inbound_raw_json)
        inbound_raw_json = re.sub(r'[\'"]{', '{', inbound_raw_json)
        inbound_raw_json = re.sub(r'}[\'"]','}', inbound_raw_json)
        inbound_dict = json.loads(inbound_raw_json)

        if use_pprint:
            message = pprint.pformat(inbound_dict, indent=4)
        else:
            message = format_dict(inbound_dict, exclude_empty=exclude_empty_fields)

        message_id = sns.publish(
            TopicArn=output_topic_arn,
            Subject=subject,
            Message=message
        )

        print("published the alert: " + str(message_id))

    return

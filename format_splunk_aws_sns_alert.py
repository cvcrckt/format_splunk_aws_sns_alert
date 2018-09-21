import boto3
from os import environ

def lambda_handler(event, context):
   print("loading handler")
   sns = boto3.client(service_name="sns")
   outout_topic_arn = environ['OUTPUT_TOPIC_ARN']
   output_fields = environ['OUTPUT_FIELDS'].split(',')
   message=''

   for output_field in map(str.strip, output_fields):
       if output_field == '__linebreak':
           message = message + '\n'
       else:
           message = message + \
           output_field + ': ' + \
           event[output_field] + '\n'

   sns.publish(
       TopicArn = outout_topic_arn,
       Message = message
   )

   return

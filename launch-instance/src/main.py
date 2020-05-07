import boto3

ec2 = boto3.client('ec2')

def lambda_handler(event, context):
    print(event)
    launch_template = {
      "LaunchTemplateId": event['LaunchTemplateId'],
      "Version": event['Version'],
    }
    response = ec2.run_instances(LaunchTemplate=launch_template, MinCount=1, MaxCount=1)
    print(response)

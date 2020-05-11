from datetime import datetime, timedelta

import boto3

BATCH = boto3.client('batch')
ECS = boto3.client('ecs')
EC2 = boto3.client('ec2')


def lambda_handler(event, context):
    compute_environment_arn = event['ComputeEnvironmentArn']

    response = BATCH.describe_compute_environments(computeEnvironments=[compute_environment_arn])
    ecs_cluster_arn = response['computeEnvironments'][0]['ecsClusterArn']

    registration_grace_timestamp = datetime.now() - timedelta(minutes=5)
    response = ECS.list_container_instances(
        cluster=ecs_cluster_arn,
        filter=f'runningTasksCount==0 and registeredAt < {registration_grace_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")}'
    )
    container_instance_arns = response['containerInstanceArns']

    if container_instance_arns:
        response = ECS.describe_container_instances(cluster=ecs_cluster_arn, containerInstances=container_instance_arns)
        ec2_instance_ids = [item['ec2InstanceId'] for item in response['containerInstances']]
        print(ec2_instance_ids)

        response = EC2.terminate_instances(InstanceIds=ec2_instance_ids)
        print(response)

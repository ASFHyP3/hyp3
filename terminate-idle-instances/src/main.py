import boto3
from datetime import datetime, timedelta

batch = boto3.client('batch')
ecs = boto3.client('ecs')
ec2 = boto3.client('ec2')


def lambda_handler(event, context):
    compute_environment_arn = event['ComputeEnvironmentArn']

    response = batch.describe_compute_environments(computeEnvironments=[compute_environment_arn])
    ecs_cluster_arn = response['computeEnvironments'][0]['ecsClusterArn']

    min_instance_age_before_delete = datetime.now() - timedelta(minutes=5)
    response = ecs.list_container_instances(
        cluster=ecs_cluster_arn, 
        filter=f'runningTasksCount==0 and registered at > {min_instance_age_before_delete.strftime("%Y-%m-%dT%H:%M:%SZ")}'
    )
    container_instance_arns = response['containerInstanceArns']

    response = ecs.describe_container_instances(cluster=ecs_cluster_arn, containerInstances=container_instance_arns)
    ec2_instance_ids = [item['ec2InstanceId'] for item in response['containerInstances']]
    print(ec2_instance_ids)

    # filters = [{
        # 'Name': 'instance-id',
        # 'Values': ec2_instance_ids,
    # }]
    # response = ec2.describe_spot_instance_requests(Filters=filters)
    # spot_instance_request_ids = [item['SpotInstanceRequestId'] for item in response['SpotInstanceRequests']]
    # print(spotInstanceRequestIds)

    response = ec2.terminate_instances(InstanceIds=ec2_instance_ids)
    print(response)

    # response = ec2.cancel_spot_instance_requests(SpotInstanceRequestIds=spot_instance_request_ids)
    # print(response)

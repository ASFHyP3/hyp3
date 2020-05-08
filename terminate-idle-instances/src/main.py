import boto3

batch = boto3.client('batch')
ecs = boto3.client('ecs')
ec2 = boto3.client('ec2')


def lambda_handler(event, context):
    compute_environment_arn = event['computeEnvironmentArn']

    response = batch.describe_compute_environments(computeEnvironments=[compute_environment_arn])
    ecs_cluster_arn = response['computeEnvironments'][0]['ecsClusterArn']

    response = ecs.list_container_instances(cluster=ecs_cluster_arn, filter='runningTasksCount==0') #and registeredAt<2020-07-18T22:28:28+00:00
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

import boto3

BATCH = boto3.client('batch')
ECS = boto3.client('ecs')
EC2 = boto3.client('ec2')


def oustanding_jobs_exist(job_queue_arn):
    for status in ['RUNNABLE', 'STARTING', 'SUBMITTED', 'PENDING']:
        response = BATCH.list_jobs(jobQueue=job_queue_arn, jobStatus=status, maxResults=1)
        if response['jobSummaryList']:
            return True
    return False


def get_idle_instance_ids(compute_environment_arn):
    response = BATCH.describe_compute_environments(computeEnvironments=[compute_environment_arn])
    ecs_cluster_arn = response['computeEnvironments'][0]['ecsClusterArn']

    response = ECS.list_container_instances(cluster=ecs_cluster_arn, filter='runningTasksCount==0')
    container_instance_arns = response['containerInstanceArns']

    idle_instance_ids = []
    if container_instance_arns:
        response = ECS.describe_container_instances(cluster=ecs_cluster_arn, containerInstances=container_instance_arns)
        idle_instance_ids = [item['ec2InstanceId'] for item in response['containerInstances']]
    return idle_instance_ids


def lambda_handler(event, context):
    if oustanding_jobs_exist(event['JobQueueArn']):
        return

    idle_instance_ids = get_idle_instance_ids(event['ComputeEnvironmentArn'])
    if idle_instance_ids:
        print(idle_instance_ids)
        response = EC2.terminate_instances(InstanceIds=idle_instance_ids)
        print(response)

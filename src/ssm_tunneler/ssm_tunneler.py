import time
import boto3
import subprocess


def open_ssm_tunnel(
    profile: str,
    region: str,
    instance_name: str,
    remote_port: int,
    remote_host: str,
    local_port: int,
):
    """
    Open an SSM tunnel to an EC2 instance.

    Args:
        profile (str): AWS profile name.
        region (str): AWS region.
        instance_name (str): Name of the EC2 instance.
        remote_port (int): Port on the remote host.
        remote_host (str): Remote host.
        local_port (int): Local port.

    Returns:
        subprocess.Popen: Process object.
    """
    session = boto3.Session(profile_name=profile, region_name=region)

    ec2 = session.client("ec2")
    response = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Name", "Values": [instance_name]},
            {"Name": "instance-state-name", "Values": ["running"]},
        ]
    )

    if not response["Reservations"]:
        raise Exception(
            f"There is no instance with the name '{instance_name}' running in the region '{region}'."
        )

    instance_id = response["Reservations"][0]["Instances"][0]["InstanceId"]

    command = [
        "aws",
        "ssm",
        "start-session",
        "--profile",
        profile,
        "--region",
        region,
        "--target",
        instance_id,
        "--document-name",
        "AWS-StartPortForwardingSessionToRemoteHost",
        "--parameters",
        f'{{"host":["{remote_host}"],"portNumber":["{remote_port}"],"localPortNumber":["{local_port}"]}}',
    ]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        time.sleep(2)
        return process
    except Exception as e:
        process.terminate()
        raise


def kill_session_manager_processes():
    """
    Kill all session-manager processes.

    Args:
        None

    Returns:
        None
    """
    ps_output = subprocess.run(["ps", "-eo", "pid,cmd"], capture_output=True, text=True)
    lines = ps_output.stdout.split("\n")
    for line in lines:
        if "session-manager" in line:
            pid = line.split()[0]
            subprocess.run(["kill", "-9", pid])

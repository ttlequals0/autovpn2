#!/usr/bin/env python
#
import argparse
import boto3
import sys
from botocore.exceptions import ClientError
import paramiko


region_to_ami = {"us-east-1": "ami-d05e75b8", "us-east-2": "ami-153e6470", "us-west-1": "ami-06116566",
                 "us-west-2": "ami-9abea4fb", "eu-west-1": "ami-f95ef58a", "eu-west-2": "ami-23d0da47", "eu-west-3": "ami-4262d53f",
                 "eu-central-1": "ami-87564feb", "ap-northeast-1": "ami-a21529cc", "ap-northeast-2": "ami-09dc1267",
                 "ap-southeast-1": "ami-25c00c46", "ap-southeast-2": "ami-6c14310f", "sa-east-1": "ami-0fb83963",
                 "ap-south-1": "ami-4a90fa25", "ca-central-1": "ami-0651e362"}

# Generate region choices
region_choices = []
for region, ami in region_to_ami.iteritems():
    region_choices.append(region)

flags = dict.fromkeys(["create", "status"], False)

# CLI arguments
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                 description='On Demand AWS OpenVPN Endpoint Deployment Tool.', epilog="Notes: \n \
	* - Customs ami may be needed if changing instance type. \n \
	** - In reality any  instance size can be given but the t2.micro is more than enough. \n \
	*** - Custom user might be need if using a custom ami. \n \
	**** - AWS IAM user must have EC2 or Administrator permissions set.")
group = parser.add_mutually_exclusive_group()
group.add_argument("-C", "--create", action='store_true',
                   help="Create VPN endpoint.")
group.add_argument("-D", "--delete_keypair",
                   action='store_true', help="Delete keypair from region.")
group.add_argument("-G", "--generate_keypair",
                   action='store_true', help="Generate new keypair.")
group.add_argument("-S", "--status", action='store_true',
                   help="Get all running instances in a given region.")
group.add_argument("-T", "--terminate", action='store_true',
                   help="Terminate a OpenVPN endpoint.")
parser.add_argument('-a', '--custom_ami', type=str, help="Specify A custom ami. *",
                    metavar='')
parser.add_argument("-d", "--custom_dns", type=str, help="Specify a custom DNS server. (ex. 4.2.2.1)",
                    metavar='')
parser.add_argument("-i", "--instance_type", type=str, help="AWS Instance type (Optional, Default is t2.micro) **",
                    metavar='')
parser.add_argument("-k", "--keypair", type=str, help="Specify the name of AWS keypair.",
                    metavar='')
parser.add_argument("-m", "--multiple_connections", type=str, help="Allow multiple connections to same endpoint.",
                    metavar='')
parser.add_argument("-r", "--region", type=str,  choices=region_choices, help='Specify AWS Region. '+', '.join(region_choices),
                    metavar='')
parser.add_argument("-p", "--custom_port", type=str,
                    help="Specify custom OpenVPN UDP port.", metavar='')
parser.add_argument("-u", "--custom_user", type=str,
                    help="Specify custom ssh user. ***", metavar='')
parser.add_argument("-y", "--auto_confirm", type=str,
                    help="Skip confirmations", metavar='')
parser.add_argument("-z", "--instance_id",  type=str,
                    help="Specify instance id.", metavar='')
args = parser.parse_args()


def deploy_instance(target_region=args.region, keypair=args.keypair):

    # Set Security Group
    security_group_name = "vpn_2"

    # Get ami for the specified region
    for region, ami in region_to_ami.items():
        if region == target_region:
            ami_id = ami

    ec2 = boto3.resource('ec2', region_name=target_region)
    client = boto3.client('ec2')

    # Create Security Group Allowing SSH and OpenVPN
    try:
        response = client.create_security_group(GroupName='vpn_2',
                                                Description='A group that allows VPN access')
        security_group_id = response['GroupId']
        print('Security Group Created %s.' % (security_group_id))
        data = client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {'IpProtocol': 'tcp',
                 'FromPort': 22,
                 'ToPort': 22,
                 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'udp',
                 'FromPort': 1194,
                 'ToPort': 1194,
                 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
            ])
        print('Ingress Successfully Set %s' % data)
    except ClientError as e:
        print(" here")

    # Create the ec2 instance and place in proper security group
    instance = ec2.create_instances(
        ImageId=ami_id,
        MinCount=1,
        MaxCount=1,
        KeyName=keypair,
        SecurityGroups=["vpn_2"],
        InstanceType='t2.micro')
    print(instance[0].id)

    # Tag newly created instance
    new_instance = []
    new_instance.append(instance[0].id)

    ec2.create_tags(
        Resources=new_instance,
        Tags=[
            {
                'Key': 'auto_vpn',
                'Value': 'auto_vpn'
            },
        ]
    )


def terminate_instance():
    '''placeholder'''

def deploy_openvpn():
    '''placeholder'''


def check_instance(target_region=args.region):
    ec2 = boto3.resource('ec2', region_name=target_region)
    client = boto3.client('ec2')

    # Create filter for power state and tag
    idfilters = [
        {
            'Name': 'instance-state-name',
            'Values': ['running']
        },
        {
            'Name': 'tag-key',
            'Values': ['auto_vpn']
        }
    ]
    # filter the instances based on filters() above
    instances = ec2.instances.filter(Filters=idfilters)

    RunningInstances = []

    for instance in instances:
        # for each instance, append to array and print instance id
        RunningInstances.append(instance.id)
    try:
        # Get ec2 public ip
        response = client.describe_instances(
            InstanceIds=[
                RunningInstances[0],
            ],
        )
        InstanceId = RunningInstances[0]
        for r in response['Reservations']:
            for i in r['Instances']:
                InstancePublicIP = (i['PublicIpAddress'])
    except:
        print("There are no instances runnting in %s" % (target_region))
        sys.exit()
    # Return Instance ID and Public IP address
    return(InstanceId, InstancePublicIP)


def create_keypair():
    '''placeholder'''


def remove_keypair():
    '''placeholder'''


for flag in flags.keys():
    flags[flag] = vars(args)[flag]


if flags['create']:
    deploy_instance()
if flags['status']:
    InstanceId, InstancePublicIP = check_instance()
    print("Instance Id:%s Public IP:%s" % (InstanceId, InstancePublicIP))

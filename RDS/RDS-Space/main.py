#!/usr/bin/env python
"""rds-create-cpu-alarms

Script used to create CPUUtilization alarms in AWS CloudWatch
for all RDS instances.
A upper-limit threshold needs to be defined.

Usage:
    rds-create-cpu-alarms [options] <threshold> <sns_topic_arn> <region>
    rds-create-cpu-alarms -h | --help

Options:
    -h --help   Show this screen.
    --debug     Don't send data to AWS

"""
import time
import boto.ec2
import boto.rds2
from docopt import docopt
from boto.ec2.cloudwatch import MetricAlarm

from constants import VERSION

DEBUG = False


def get_rds_instances(region):
    """
    Retrieves the list of all RDS instances

    Args:
        region (str)

    Returns:
        (list) List of valid state RDS instances
    """
    assert isinstance(region, str)

    rds = boto.rds2.connect_to_region(region)
    response = rds.describe_db_instances()
    rds_instances = (response[u'DescribeDBInstancesResponse']
                             [u'DescribeDBInstancesResult']
                             [u'DBInstances']
                     )
    return rds_instances


def get_existing_cpuutilization_alarm_names(aws_cw_connect):
    """
    Creates a CPUUtilization alarm for all RDS instances

    Args:
        aws_cw_connect (CloudWatchConnection)

    Returns:
        (set) Existing CPUUtilization alarm names
    """
    assert isinstance(aws_cw_connect,
                      boto.ec2.cloudwatch.CloudWatchConnection)

    existing_alarms = aws_cw_connect.describe_alarms()
    existing_alarm_names = set()

    for existing_alarm in existing_alarms:

        existing_alarm_names.add(existing_alarm.name)

    return existing_alarm_names


def get_cpuutilization_alarms_to_create(rds_instances,
                                        threshold,
                                        aws_cw_connect,
                                        sns_topic_arn):
    """
    Creates a CPUUtilization alarm for all RDS instances

    Args:
        rds_instances (list) List of all RDS instances
        threshold (int) The upper limit after which alarm activates
        aws_cw_connect (CloudWatchConnection)
        sns_topic_arn (str)

    Returns:
        (set) All CPUUtilization alarms that will be created
    """
    assert isinstance(rds_instances, list)
    assert isinstance(aws_cw_connect,
                      boto.ec2.cloudwatch.CloudWatchConnection)
    assert isinstance(threshold, int)
    assert isinstance(sns_topic_arn, str)

    alarms_to_create = set()
    existing_alarms = get_existing_cpuutilization_alarm_names(aws_cw_connect)

    for instance in rds_instances:

        # initiate a CPUUtilization MetricAlarm object for each RDS instance
        cpu_utilization_alarm = MetricAlarm(
            name=u'RDS-{}-Low-Free-Storage-Space'.format(
                instance[u'DBInstanceIdentifier']
            ),
            namespace=u'AWS/RDS',
            metric=u'FreeStorageSpace', statistic='Average',
            comparison=u'<',
            threshold=(0.20*instance[u'AllocatedStorage'])*1000000000,
            period=60, evaluation_periods=10,
            alarm_actions=[sns_topic_arn],
            dimensions={u'DBInstanceIdentifier':
                        instance[u'DBInstanceIdentifier']
                        }
        )

        if cpu_utilization_alarm.name not in existing_alarms:
            alarms_to_create.add(cpu_utilization_alarm)

    return alarms_to_create


def main():
    args = docopt(__doc__, version=VERSION)

    global DEBUG

    if args['--debug']:
        DEBUG = True

    region = args['<region>']

    sns_topic_arn = args['<sns_topic_arn>']

    rds_instances = get_rds_instances(region)
    aws_cw_connect = boto.ec2.cloudwatch.connect_to_region(region)
    alarms_to_create = get_cpuutilization_alarms_to_create(
        rds_instances,
        int(args['<threshold>']),
        aws_cw_connect,
        sns_topic_arn
    )

    if alarms_to_create:
        if DEBUG:
            for alarm in alarms_to_create:
                print 'DEBUG:', alarm
        else:
            print 'New RDS CPUUtilization Alarms created:'
            for alarm in alarms_to_create:
                print alarm
                time.sleep(1)
                aws_cw_connect.create_alarm(alarm)


if __name__ == '__main__':

    main()

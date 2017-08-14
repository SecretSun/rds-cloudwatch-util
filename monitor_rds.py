import json
import boto3
from boto import rds2
from boto.ec2.cloudwatch import MetricAlarm

def createConnection(aws_region):
    connection = rds2.connect_to_region(aws_region)
    return connection

def constructARN(region):

    region_name = region
    iam = boto3.resource('iam')
    # i have to check whether the account id is global or corresponds to a particular user
    account_id = iam.CurrentUser().arn.split(':')[4]
    rds_arn = "arn:aws:rds:"+region_name+":"+account_id+":db:"
    return rds_arn
       
def getAllTagsInGivenRegion(region):
    
    conn = createConnection(region)
    status_map = {}
    response = conn.describe_db_instances()
    instances = response['DescribeDBInstancesResponse']['DescribeDBInstancesResult']['DBInstances']
    for instance in instances:
        instance_identifier = instance['DBInstanceIdentifier']
        rds_arn_name = constructARN(region)
        arn_name = rds_arn_name+instance_identifier
        # print arn_name
        tag_list = conn.list_tags_for_resource(arn_name)
        tags = tag_list['ListTagsForResourceResponse']['ListTagsForResourceResult']
        # list = []
        # for each_tag in tags["TagList"]:
        #     temp_json = {}
        #     temp_json[each_tag["Key"]] = each_tag["Value"]
        #     list.append(temp_json)
        status_map[instance['DBInstanceIdentifier']] = tags["TagList"]
  
    return status_map

def createFreeStorageAlarms(tags):
    
    storage_alarm = MetricAlarm(
        name=u'RDS-{}-Low-Free-Storage-Space'.format(
            instance[u'DBInstanceIdentifier']),
        namespace=u'AWS/RDS',
        metric=u'FreeStorageSpace', statistic='Average',
        comparison=u'<',
        threshold=(0.20*instance[u'AllocatedStorage'])*1000000000,
        period=60, evaluation_periods=5,
        alarm_actions=[u'arn:aws:sns:us-west-1:667005031541:ops'],
        dimensions={u'DBInstanceIdentifier':
                    instance[u'DBInstanceIdentifier']})
    

def main():
    
    region = raw_input("what is the region name to monitor?")
    service = raw_input("which service you want to monitor(currently supported rds)?")
    print "you want to monitor %s service in this %s region" %(service, region)
    getTags = getAllTagsInGivenRegion(region)
    print json.dumps(getTags)
    #alarms_to_create = createFreeStorageAlarms(getTags)



if __name__ == '__main__':
    
    main()
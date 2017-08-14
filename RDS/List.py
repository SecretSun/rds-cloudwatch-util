import boto3
from boto3.session import Session

s = Session()
rds_regions = s.get_available_regions('lambda')

for region in rds_regions:
    print('=================================Region: '+region+' ==============')
    rds_client = boto3.client('rds',region_name=region)
#    cloudwatch = boto3.client('cloudwatch',region_name=region)
#    print rds_client
    rds_list = rds_client.describe_db_instances();
    for rds_func in rds_list['DBInstances']:
         print(rds_func['DBInstanceIdentifier'])

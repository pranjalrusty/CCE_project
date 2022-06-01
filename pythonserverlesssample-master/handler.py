import boto3
import os
import pandas as pd
import logging

db_client = boto3.client('dynamodb')
s3 = boto3.client('s3')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def importCSVToDB(event, context):
    logger.info('got event{}'.format(event))

    documents_table = os.environ['documentsTable']
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    file_key = event['Records'][0]['s3']['object']['key']

    logger.info('Reading {} from {}'.format(file_key, bucket_name))

    csv = s3.get_object(Bucket=bucket_name, Key=file_key)

    df = pd.read_csv(csv['Body'], skip_blank_lines=True,
                     usecols=['REGISTER_NAME', 'AFS_LIC_NUM', 'AFS_LIC_NAME', 'AFS_LIC_ADD_LOCAL',
                              'AFS_LIC_ADD_STATE', 'AFS_LIC_ADD_PCODE'])

    df = df.astype(str)
    df = df.fillna("NA")
    values = df.T.to_dict().values()

    for value in values:
        if value["AFS_LIC_NUM"]:
            last_updated = value["AFS_LIC_NAME"]
            db_client.update_item(
                TableName=documents_table,
                Key={
                    'id': {"S": value["AFS_LIC_NUM"]}
                },
                UpdateExpression="set reg_name = :r",
                ExpressionAttributeValues={
                    ':r': {"S": value['AFS_LIC_NAME']},
                },
                ReturnValues="UPDATED_NEW"
            )

    logger.info('last updated register {}'.format(last_updated))

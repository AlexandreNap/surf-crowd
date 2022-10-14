import json
import pymongo
import certifi
from SECRET_VARS import *
import utils
from datetime import datetime, timezone
import boto3


def lambda_handler(event, context):
    client = pymongo.MongoClient(MONGO_ADRESS, tlsCAFile=certifi.where())
    bucket = boto3.resource('s3')
    utils.s3_to_mongodb_sviews(bucket, client, datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d"))

    return {
        'statusCode': 200
    }
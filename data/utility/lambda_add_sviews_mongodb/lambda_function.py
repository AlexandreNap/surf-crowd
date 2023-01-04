import json
import pymongo
import certifi
from SECRET_VARS import *
import utils
from datetime import datetime, timezone


def lambda_handler(event, context):
    client = pymongo.MongoClient(MONGO_ADRESS, tlsCAFile=certifi.where())
    bucket = utils.bucket_resource()
    utils.s3_to_mongodb_sviews(bucket, client, datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d"))

    return {
        'statusCode': 200
    }

import pymongo
import certifi
import boto3
from SECRET_VARS import *
import re

TEST = ""


def get_spots():
    return ["Lacanau",
            "Biarritz",
            "Capbreton_Prevent",
            "Capbreton_Santosha",
            "Anglet_GrandePlage"
            ]


def s3_sview_to_spot(path):
    spot = re.search(r'spots/(.*?)/.*', path).group(1)
    return spot


def s3_sview_to_dt(path):
    date_time = re.search(r'spots/.*?/(.*).jpg', path).group(1)
    return date_time


def s3_path(path):
    return path


def mongo_client():
    client = pymongo.MongoClient(MONGO_ADRESS, tlsCAFile=certifi.where())
    return client


def get_mongo_stored_sviews(client, date=""):
    db = client["surf" + TEST]
    col = db["sviews"]
    my_list = []
    # add use of optional date_range
    query = None
    if date != "":
        query = {"date": date}
    for x in col.find(query):
        my_list.append(x)
    return my_list


def store_mongo_new_sviews(client, sviews):
    db = client["surf" + TEST]
    col = db["sviews"]
    item_list = []
    for sview in sviews:
        dt = s3_sview_to_dt(sview)
        date = dt[:10]
        item_list.append({"spot_name": s3_sview_to_spot(sview),
                        "date_time": dt,
                        "date": date,
                        "s3_path": s3_path(sview)})
    col.insert_many(item_list)


def bucket_resource():
    s3 = boto3.resource('s3',
                        aws_access_key_id=AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=AWS_ACCESS_KEY_SECRET,
                        region_name="eu-west-3"
                        )
    bucket = s3.Bucket(AWS_BUCKET)
    return bucket


def get_s3_stored_sviews(bucket, prefix_date="", reverse=False):
    all_objects = []
    for spot in get_spots():
        prefix = f'spots/{spot}/{prefix_date}'
        objs = [obj for obj in bucket.objects.filter(Prefix=prefix).all()]
        all_objects += objs

    if reverse:
        def get_last_modified(obj): return obj.last_modified.strftime('%Y-%m-%d %H-%M-%S')
        all_objects = [obj for obj in sorted(all_objects, key=get_last_modified)]
    return [obj.key for obj in all_objects]


def s3_to_mongodb_sviews(bucket, client, date=""):
    s3_path_list = get_s3_stored_sviews(bucket, date)
    mongodb_list = get_mongo_stored_sviews(client, date)
    mongodb_path_list = [item["s3_path"] for item in mongodb_list if "s3_path" in item]

    items_to_add = [s3_path for s3_path in s3_path_list if s3_path not in mongodb_path_list]

    store_mongo_new_sviews(client, items_to_add)

import boto3
from botocore.client import Config
import sys
import os
import re

s3_compatible_endpoint_url = sys.argv[1]
access_key = os.environ['ACCESS_KEY']
secret_access_key = os.environ['SECRET_KEY']
bucket_name = sys.argv[2]
subdirectory_name = f"{sys.argv[3]}"
date_string = sys.argv[4]
search_string = f"{subdirectory_name}/PXL_{date_string}"
session = boto3.session.Session()
target_directory = sys.argv[5]
print(search_string)
# Create an S3 client with the session
s3_client = session.client(
    service_name='s3',
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_access_key,
    endpoint_url=s3_compatible_endpoint_url,
    config=Config(signature_version='s3v4'),
    region_name='us-west-1'
)

def get_object_list():
  paginator = s3_client.get_paginator('list_objects_v2')
  
  page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=search_string)
  objects_list = []
  for page in page_iterator:
      if 'Contents' in page:  # Check if there are objects in the page
          for obj in page['Contents']:
              #print(obj['Key'])
              objects_list.append(obj['Key'])
          return objects_list
      else:
          print(f"No objects found.")

def download_objects(object_list):
  for object in objects:
      stripped_filename = object.lstrip(f'{subdirectory_name}/')
      try:
         os.makedirs(f"{target_directory}/{date_string}", exist_ok=True)
      except:
         pass
      with open(f"{target_directory}/{date_string}/{stripped_filename}", 'wb') as f:
        s3_client.download_fileobj(bucket_name, object, f)

objects = get_object_list()
download_objects(objects)
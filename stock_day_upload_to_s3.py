import boto3
import os

client = boto3.client('s3')
for dir_path, dirs, files in os.walk("./data"):
    for file_name in files:
        file_path = os.path.join(dir_path, file_name)
        if file_path.endswith(".csv"):
            # print(file_path)
            client.upload_file(file_path, 'stock-ej04xjp6', file_name)
            client.put_object_acl(ACL='public-read', Bucket='stock-ej04xjp6', Key=file_name)

import os

from dotenv import load_dotenv
import boto3
import time
import requests

from hello import MedicalImagingWrapper

load_dotenv()

DATASTORE_ID = os.environ["AHI_DATASTORE_ID"]
S3_URI = os.environ["S3_URI"]

client = MedicalImagingWrapper(boto3.client("medical-imaging"))

LOOPS = 10
image_set_id = "01a726342222ee43e5a0fe375f5dd2a7"
frame_id = "faae2cb1554b0ff00f4c569a74898909"
start_time = time.time()
for i in range(LOOPS):
    pixel_data = client.get_pixel_data(DATASTORE_ID, image_set_id, frame_id)
end_time = time.time()

execution_time = (end_time - start_time) / LOOPS
print(
    f"AHI Pixel Data Execution time: {execution_time} seconds, {len(pixel_data)} bytes"
)

s3_client = boto3.client("s3")
s3_uri_parts = S3_URI.split("/")
bucket_name = s3_uri_parts[2].split(".")[0]
file_key = "/".join(s3_uri_parts[3:])
start_time = time.time()
for i in range(LOOPS):
    object = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    boto_response = object["Body"].read()
end_time = time.time()

execution_time = (end_time - start_time) / LOOPS
print(f"Boto S3 Execution time: {execution_time} seconds, {len(boto_response)} bytes")

start_time = time.time()
for i in range(LOOPS):
    response = requests.get(S3_URI)
end_time = time.time()

execution_time = (end_time - start_time) / LOOPS
print(
    f"Requests S3 Execution time: {execution_time} seconds, {len(response.content)} bytes"
)

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

image_set_id = "01a726342222ee43e5a0fe375f5dd2a7"
frame_id = "faae2cb1554b0ff00f4c569a74898909"
start_time = time.time()
pixel_data = client.get_pixel_data(DATASTORE_ID, image_set_id, frame_id)
end_time = time.time()

execution_time = end_time - start_time
print(
    f"AHI Pixel Data Execution time: {execution_time} seconds, {len(pixel_data)} bytes"
)

start_time = time.time()
response = requests.get(S3_URI)
end_time = time.time()

execution_time = end_time - start_time
print(f"S3 Execution time: {execution_time} seconds, {len(response.content)} bytes")

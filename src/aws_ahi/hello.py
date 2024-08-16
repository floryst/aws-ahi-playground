import logging
import gzip
import math
import os
import json
from pprint import pprint

from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
logger = logging.getLogger(__name__)

DATASTORE_ID = os.environ["AHI_DATASTORE_ID"]

# adapted from the AHI documentation
class MedicalImagingWrapper:
    def __init__(self, health_imaging_client):
        self.health_imaging_client = health_imaging_client

    def search_image_sets(self, datastore_id, search_filter=None, limit=math.inf):
        """
        Search for image sets.

        :param datastore_id: The ID of the data store.
        :param search_filter: The search filter.
            For example: {"filters" : [{ "operator": "EQUAL", "values": [{"DICOMPatientId": "3524578"}]}]}.
        :return: The list of image sets.
        """
        try:
            paginator = self.health_imaging_client.get_paginator("search_image_sets")
            page_iterator = paginator.paginate(
                datastoreId=datastore_id, searchCriteria=search_filter or {}
            )
            metadata_summaries = []
            for page in page_iterator:
                metadata_summaries.extend(page["imageSetsMetadataSummaries"])
                if len(metadata_summaries) >= limit:
                    break
        except ClientError as err:
            logger.error(
                "Couldn't search image sets. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            if limit == math.inf:
                return metadata_summaries
            return metadata_summaries[:limit]

    def get_image_set(self, datastore_id, image_set_id, version_id=None):
        """
        Get the properties of an image set.

        :param datastore_id: The ID of the data store.
        :param image_set_id: The ID of the image set.
        :param version_id: The optional version of the image set.
        :return: The image set properties.
        """
        try:
            if version_id:
                image_set = self.health_imaging_client.get_image_set(
                    imageSetId=image_set_id,
                    datastoreId=datastore_id,
                    versionId=version_id,
                )
            else:
                image_set = self.health_imaging_client.get_image_set(
                    imageSetId=image_set_id, datastoreId=datastore_id
                )
        except ClientError as err:
            logger.error(
                "Couldn't get image set. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            return image_set

    def get_image_set_metadata(self, datastore_id, image_set_id, version_id=None):
        """
        Get the metadata of an image set.

        :param datastore_id: The ID of the data store.
        :param image_set_id: The ID of the image set.
        :param version_id: The version of the image set.
        """
        try:
            if version_id:
                image_set_metadata = self.health_imaging_client.get_image_set_metadata(
                    imageSetId=image_set_id,
                    datastoreId=datastore_id,
                    versionId=version_id,
                )
            else:

                image_set_metadata = self.health_imaging_client.get_image_set_metadata(
                    imageSetId=image_set_id, datastoreId=datastore_id
                )

            assert image_set_metadata["contentType"] == "application/json"
            assert image_set_metadata["contentEncoding"] == "gzip"
            with gzip.open(image_set_metadata["imageSetMetadataBlob"]) as gfp:
                return json.loads(gfp.read())

        except ClientError as err:
            logger.error(
                "Couldn't get image metadata. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    def get_pixel_data(self, datastore_id, image_set_id, image_frame_id):
        """
        Get an image frame's pixel data.

        :param datastore_id: The ID of the data store.
        :param image_set_id: The ID of the image set.
        :param image_frame_id: The ID of the image frame.
        """
        try:
            image_frame = self.health_imaging_client.get_image_frame(
                datastoreId=datastore_id,
                imageSetId=image_set_id,
                imageFrameInformation={"imageFrameId": image_frame_id},
            )

            assert image_frame['contentType'] == 'application/octet-stream'
            return image_frame['imageFrameBlob'].read()
        except ClientError as err:
            logger.error(
                "Couldn't get image frame. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise


client = MedicalImagingWrapper(boto3.client("medical-imaging"))

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    # might want to default to the default set of CORS enabled headers
    # to mimic a real-world scenario (i.e. Content-Range can be CORS-blocked)
    #allow_headers=['*'],
    allow_credentials=True,
)

@app.get("/list-image-sets")
def list_image_sets():
    image_sets = []
    for image_set in client.search_image_sets(DATASTORE_ID, limit=100):
        dicom_tags = image_set['DICOMTags']
        image_sets.append({
            'imageSetId': image_set['imageSetId'],
            'PatientId': dicom_tags.get('DICOMPatientId', None),
            'PatientName': dicom_tags.get('DICOMPatientName', None),
            'PatientSex': dicom_tags.get('DICOMPatientSex', None),
            'PatientBirthDate': dicom_tags.get('DICOMPatientBirthDate', None),
            'StudyDate': dicom_tags.get('DICOMStudyDate', None),
            'StudyDescription': dicom_tags.get('DICOMStudyDescription', None),
            'StudyId': dicom_tags.get('DICOMStudyId', None),
            'StudyInstanceUID': dicom_tags['DICOMStudyInstanceUID'],
        })
    return image_sets

@app.get("/image-set/{image_set_id}")
def get_image_set(image_set_id: str):
    return client.get_image_set_metadata(DATASTORE_ID, image_set_id)

@app.get("/image-set/{image_set_id}/{frame_id}/pixel-data")
def get_pixel_data(image_set_id: str, frame_id: str):
    pixel_data = client.get_pixel_data(DATASTORE_ID, image_set_id, frame_id)
    return Response(media_type='application/octet-stream', content=pixel_data)

# used for exploration/debugging
def main():
    for image_set in client.search_image_sets(DATASTORE_ID, limit=1):
        # print("-" * 8)

        image_set_id = image_set["imageSetId"]
        # print(f"> Image set {image_set_id}:")
        pprint(image_set)

        metadata = client.get_image_set_metadata(DATASTORE_ID, image_set_id)
        # print("> Metadata:")
        patient = metadata["Patient"]
        study = metadata["Study"]
        series = study["Series"]

        for series_uid in series:
            single_series = series[series_uid]
            print(f'Series UID: {series_uid}')
            print(f' Number of instances: {len(single_series['Instances'])}')
        
        # only look at the first one
        series_uid = next(iter(series.keys()))
        single_series = series[series_uid]
        instances = single_series['Instances']
        print(f'Looking at series: {series_uid}')
        print(f'Number of instances: {len(instances)}')

        # pick first instance
        instance_id = next(iter(instances.keys()))
        instance = instances[instance_id]
        num_frames = len(instance["ImageFrames"])
        print(f'Number of frames: {num_frames}')

        # pick middle frame
        frame = instance['ImageFrames'][num_frames // 2]
        pixel_data = client.get_pixel_data(DATASTORE_ID, image_set_id, frame['ID'])

        print(type(pixel_data), len(pixel_data))

        with open('frame.bin', 'wb') as fp:
            fp.write(pixel_data)
        print('Wrote out a single HTJ2K frame to frame.bin')

if __name__ == "__main__":
    main()

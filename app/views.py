from functools import lru_cache
import certifi
from bson.json_util import dumps
from bson import ObjectId
import json

from pymongo.mongo_client import MongoClient
from pymongo.database import Database

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


@lru_cache(maxsize=1, typed=False)
def _get_db() -> Database:
    uri = (
        "mongodb+srv://bloodbank_studio:iUVOduZpPwyzqnUc@database-cluster."
        "x8jh9wc.mongodb.net/?retryWrites=true&w=majority"
    )
    client = MongoClient(uri, tlsCAFile=certifi.where())
    try:
        client.admin.command('ping')
    except Exception as e:
        print("Error occured on database connection: " + e)
    return client.get_database("test")


@api_view(['GET'])
def get_blood_requests(request):
    db = _get_db()
    coll = db.get_collection("blood_requests")
    blood_requests = coll.find()  # get all requests
    blood_requests_resp = []
    for blood_request in blood_requests:
        blood_requests_resp.append(
            {
                "_id": str(blood_request["_id"]),
                "name": blood_request["name"],
                "surname": blood_request["surname"],
                "blood_product_type": blood_request["blood_product_type"],
                "city": blood_request["city"],
                "district": blood_request["district"],
                "contact_gsm": blood_request["contact_gsm"]
            }
        )
    return JsonResponse(data=blood_requests_resp, status=200, safe=False)

@api_view(['POST'])
def post_blood_requests(request):
    client = _get_db()
    collection = client['blood_requests']
    data=json.loads(request.body)
    collection.insert_one(data)
    return  HttpResponse(status=200)

@api_view(['GET'])
def get_blood_request_details(request, id):
    client = _get_db()
    coll = client.get_collection("blood_requests")
    blood_request = coll.find({"_id": ObjectId(id)}).next()
    blood_request["_id"] = str(blood_request["_id"])
    return JsonResponse(data=blood_request, status=200)

@api_view(['DELETE'])
def delete_blood_request(request, object_id):
    client = _get_db()
    collection = client['blood_requests']
    collection.delete_one({'_id': ObjectId(object_id)})
    return HttpResponse(status=200)
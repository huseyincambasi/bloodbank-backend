from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from pymongo.mongo_client import MongoClient
from pymongo.database import Database
from bson.json_util import dumps
from bson import ObjectId
import mongomock
import json
import certifi

# Create your views here.

def _get_db() -> Database:
    uri = (
        "mongodb+srv://bloodbankuser:2wnLaW88aALagS8K@cluster0.xefuk3n.mongodb.net/?retryWrites=true&w=majority"
    )
    client = MongoClient(uri, tlsCAFile=certifi.where())
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    return client.get_database("bloodbank")

def main_page(request):
    context = { }
    return render(request, "index.html", context)

@api_view(['GET', 'POST'])
def dataroute(request):
    if request.method == 'GET':
        client = _get_db();
        collection = client['task']
        cursor = collection.find({})
        json_data = dumps(list(cursor))
        return HttpResponse(json_data,content_type="application/json")

    if request.method == 'POST':
        client = _get_db();
        collection = client['task']
        data=json.loads(request.body)
        collection.insert_one(data);
        return  HttpResponse(status=200)
        
@api_view(['DELETE'])
def deleteroute(request,id):
    if request.method == 'DELETE':
        client = _get_db();
        collection = client['task']
        result = client.db.collection.delete_one({'id': id})
        return  HttpResponse(status=200)
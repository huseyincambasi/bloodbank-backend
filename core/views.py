from pymongo.mongo_client import MongoClient
from pymongo.database import Database
import certifi
from django.shortcuts import render


def _get_db() -> Database:
    uri = (
        "mongodb+srv://bloodbank_studio:iUVOduZpPwyzqnUc@database-cluster."
        "x8jh9wc.mongodb.net/?retryWrites=true&w=majority"
    )
    # Create a new client and connect to the server
    client = MongoClient(uri, tlsCAFile=certifi.where())
    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    return client.get_database("polls")


# Create your views here.
def main_route(request):
    db = _get_db()
    db.list_collection_names()
    return render(request, "index.html")

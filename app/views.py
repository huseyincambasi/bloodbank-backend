from typing import List, Union
from functools import lru_cache
import certifi
import hashlib
from bson import ObjectId
import json
from datetime import timedelta, date
from uuid import uuid4

from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from pymongo.mongo_client import MongoClient
from pymongo.database import Database

from django.http import HttpResponse, JsonResponse

from rest_framework.decorators import api_view
from django_jwt_extended.exceptions import InvalidRequest
from django_jwt_extended import create_access_token
from django_jwt_extended import create_refresh_token
from django_jwt_extended import get_jwt_identity

# HELPER FUNCTIONS START


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
        print("Error occurred on database connection: ")
        raise e
    return client.get_database("test")


def send_mail(
        to_whom: Union[str, List[str]], subject: str, body: str,
        username: str = "blooddonationhelper@hotmail.com",
        password: str = "12Qwe.34",
        sender: str = "blooddonationhelper@hotmail.com",
        sender_name: str = "Blood Bank Notification System",
        host: str = "smtp.office365.com", body_type: str = "html"
):
    """
    Sends mail
    """
    host = host
    port = 587
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr((sender_name, sender))
    if isinstance(to_whom, list):
        msg["To"] = ", ".join(to_whom)
    else:
        msg["To"] = to_whom
    body = MIMEText(body, body_type)
    msg.attach(body)
    server = SMTP(host, port)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(username, password)
    server.sendmail(sender, to_whom, msg.as_string())
    server.close()


# HELPER FUNCTIONS END
# USER PAGE START


@api_view(['GET'])
def index(request):
    email = None
    try:
        email = request.session["user"]
        return JsonResponse(data={"user": email}, status=200)
    except KeyError:
        return JsonResponse(data={"user": email}, status=200)


@api_view(['POST'])
def register(request):
    db = _get_db()
    users_collection = db.get_collection("users")
    new_user = json.loads(json.dumps(request.POST))
    new_user['password'] = hashlib.sha256(new_user['password'].encode('utf-8')).hexdigest()
    doc = users_collection.find_one({'email': new_user['email']})

    if not doc:
        users_collection.insert_one(new_user)
        del new_user['password']
        new_user['_id'] = str(new_user['_id'])
        return JsonResponse(data=new_user, status=201, safe=False)
    else:
        return JsonResponse(data={'error': 'Email address already exists'}, status=409, safe=False)


@api_view(['POST'])
def login(request):
    db = _get_db()
    users_collection = db.get_collection("users")
    data = json.loads(request.body)
    user_from_db = users_collection.find_one({'email': data['email']})

    if user_from_db:
        encrypted_password = hashlib.sha256(data['password'].encode('utf-8')).hexdigest()
        if encrypted_password == user_from_db['password']:
            del user_from_db['password']
            user_from_db['_id'] = str(user_from_db['_id'])
            return JsonResponse(
                data={
                    "access_token": create_access_token(identity=user_from_db['email']),
                    'refresh_token': create_refresh_token(identity=user_from_db['email']),
                    'user': user_from_db
                },
                status=200,
                safe=False
            )
    return JsonResponse(data={'error': 'Incorrect email address or password'}, status=401, safe=False)


@api_view(['POST'])
def reset_password(request):
    db = _get_db()
    coll = db.get_collection("users")
    data = json.loads(request.body)
    email = data["email"]
    user_iter = coll.find({"email": email})
    try:
        user = user_iter.next()
    except StopIteration:
        return HttpResponse(content="user not found", status=409)
    new_password = str(uuid4())
    coll.update_one(
        filter={"email": email}, upsert=True,
        update={"$set": {"password": new_password}}
    )

    mail_body = f"""
        <html>
          <head>
            <meta charset="UTF-8">
          </head>
          <body>
            <h1> Hello {user['name']} {user['surname']}!</h1>
            <p><strong>Your new password is: {new_password}</p>
          </body>
        </html>
    """

    send_mail(
        to_whom=user["email"],
        subject="Password Reset", body=mail_body
    )

    return HttpResponse(status=200)


@api_view(['POST'])
def update_password(request):
    try:
        email = get_jwt_identity(request)
        if not email:
            return HttpResponse(content="user not logged in", status=401)
    except InvalidRequest:
        return HttpResponse(content="user not logged in", status=401)

    db = _get_db()
    coll = db.get_collection("users")
    user_iter = coll.find({"email": email})
    user = user_iter.next()
    data = json.loads(request.body)
    password = hashlib.sha256(data['password'].encode('utf-8')).hexdigest()
    new_password = data["new_password"]

    if password != user["password"]:
        return HttpResponse(content="password not true", status=409)
    
    coll.update_one(
        filter={"email": email}, upsert=True,
        update={"$set": {"password": new_password}}
    )

    return HttpResponse(status=200)


@api_view(['POST'])
def logout(request):
    request.session["user"] = None
    return HttpResponse(status=200)


@api_view(['GET'])
def user_info(request):
    try:
        email = get_jwt_identity(request)
        if not email:
            return HttpResponse(content="user not logged in", status=401)
    except InvalidRequest:
        return HttpResponse(content="user not logged in", status=401)

    client = _get_db()
    coll = client.get_collection("users")
    user = coll.find({"email": email}).next()
    user["_id"] = str(user["_id"])
    return JsonResponse(data=user, status=200, safe=False)



@api_view(['POST'])
def user_update_donation_date(request):
    try:
        email = get_jwt_identity(request)
        if not email:
            return HttpResponse(content="user not logged in", status=401)
    except InvalidRequest:
        return HttpResponse(content="user not logged in", status=401)

    data = json.loads(request.body)
    client = _get_db()
    coll = client.get_collection("users")
    coll.update_one(
        filter={"email": email}, upsert=True,
        update={"$set": {"donation_date": data["donation_date"]}}
    )
    return HttpResponse(status=200)


@api_view(['POST'])
def user_update_city(request):
    try:
        email = get_jwt_identity(request)
        if not email:
            return HttpResponse(content="user not logged in", status=401)
    except InvalidRequest:
        return HttpResponse(content="user not logged in", status=401)

    data = json.loads(request.body)
    client = _get_db()
    coll = client.get_collection("users")
    coll.update_one(
        filter={"email": email}, upsert=True,
        update={"$set": {"city": data["city"]}}
    )
    return HttpResponse(status=200)


@api_view(['POST'])
def user_update_district(request):
    try:
        email = get_jwt_identity(request)
        if not email:
            return HttpResponse(content="user not logged in", status=401)
    except InvalidRequest:
        return HttpResponse(content="user not logged in", status=401)

    data = json.loads(request.body)
    client = _get_db()
    coll = client.get_collection("users")
    coll.update_one(
        filter={"email": email}, upsert=True,
        update={"$set": {"district": data["district"]}}
    )
    return HttpResponse(status=200)


@api_view(['POST'])
def user_update_phone(request):
    try:
        email = get_jwt_identity(request)
        if not email:
            return HttpResponse(content="user not logged in", status=401)
    except InvalidRequest:
        return HttpResponse(content="user not logged in", status=401)

    data = json.loads(request.body)
    client = _get_db()
    coll = client.get_collection("users")
    coll.update_one(
        filter={"email": email}, upsert=True,
        update={"$set": {"phone": data["phone"]}}
    )
    return HttpResponse(status=200)


@api_view(['PUT'])
def user_update_info(request):
    try:
        email = get_jwt_identity(request)
        if not email:
            return HttpResponse(content="user not logged in", status=401)
    except InvalidRequest:
        return HttpResponse(content="user not logged in", status=401)

    data = json.loads(request.body)
    client = _get_db()
    coll = client.get_collection("users")
    keys = list(data.keys())
    for key in keys:
        if key in ["email", "password"]:
            data.pop(key)
    coll.update_one(
        filter={"email": email}, upsert=True,
        update={
            "$set": data
        }
    )
    return HttpResponse(status=200)


@api_view(['POST'])
def user_subscribe_or_unsubscribe(request):
    try:
        email = get_jwt_identity(request)
        if not email:
            return HttpResponse(content="user not logged in", status=401)
    except InvalidRequest:
        return HttpResponse(content="user not logged in", status=401)

    client = _get_db()
    coll = client.get_collection("users")
    user = coll.find({"email": email}).next()
    notification = user["notification"]
    if notification:
        coll.update_one(
            filter={"email": email}, upsert=True,
            update={"$set": {"notification": 0}}
        )
        return HttpResponse(content="you are unsubscribed", status=200)
    else:
        if not (user["city"] and user["district"] and user["donation_date"]):
            return HttpResponse(
                content="city district or donation date is empty", status=409
            )
        coll.update_one(
            filter={"email": email}, upsert=True,
            update={"$set": {"notification": 1}}
        )
        return HttpResponse(content="you are subscribed", status=200)


@api_view(['POST'])
def user_add_blood_request(request):
    try:
        email = get_jwt_identity(request)
        if not email:
            return HttpResponse(content="user not logged in", status=401)
    except InvalidRequest:
        return HttpResponse(content="user not logged in", status=401)

    client = _get_db()
    blood_requests_coll = client["blood_requests"]
    users_coll = client["users"]
    requester = users_coll.find({"email": email}).next()
    data = json.loads(request.body)
    data["email"] = requester["email"]
    data["name"] = requester["name"]
    data["surname"] = requester["surname"]
    data["phone"] = requester["phone"]
    result = blood_requests_coll.insert_one(data)

    inserted_id = str(result.inserted_id)
    url = f"https://bloodbank-qx6x.onrender.com/bloodrequest/{inserted_id}/"
    users_iter = users_coll.find(
        {"city": data["city"],
         "district": data["district"],
         "blood_group": data["blood_group"]}
    )
    mail_body = f"""
        <html>
          <head>
            <meta charset="UTF-8">
          </head>
          <body>
            <h1> {data['name']} {data['surname']} needs your help!</h1>
            <p><strong>Address:</strong> {data['address']}</p>
            <p><strong>Phone:</strong> {data['phone']}</p>
            <p><strong>Email:</strong> {data['email']}</p>
            <a href={url}>Visit Blood Request!</a> 
          </body>
        </html>
    """
    for user in users_iter:
        donation_date = user["donation_date"]
        if donation_date:
            if donation_date < str(date.today() - timedelta(days=90)):
                send_mail(
                    to_whom=user["email"],
                    subject="Blood Request Waiting!!!", body=mail_body
                )
    return HttpResponse(status=200)


@api_view(['GET'])
def user_blood_requests(request):
    try:
        email = get_jwt_identity(request)
        if not email:
            return HttpResponse(content="user not logged in", status=401)
    except InvalidRequest:
        return HttpResponse(content="user not logged in", status=401)

    db = _get_db()
    coll = db.get_collection("blood_requests")
    blood_requests = coll.find({"email": email})  # get requests of user
    blood_requests_resp = []
    for blood_request in blood_requests:
        blood_requests_resp.append(
            {
                "_id": str(blood_request["_id"]),
                "name": blood_request["name"],
                "surname": blood_request["surname"],
                "blood_product_type": blood_request["blood_product_type"],
                "blood_group": blood_request["blood_group"],
                "city": blood_request["city"],
                "district": blood_request["district"],
                "phone": blood_request["phone"],
                "email": blood_request["email"],
                "unit": blood_request["unit"]
            }
        )
    return JsonResponse(data=blood_requests_resp, status=200, safe=False)


@api_view(['GET'])
def user_blood_request_details(request, blood_request_id):
    try:
        email = get_jwt_identity(request)
        if not email:
            return HttpResponse(content="user not logged in", status=401)
    except InvalidRequest:
        return HttpResponse(content="user not logged in", status=401)

    client = _get_db()
    coll = client.get_collection("blood_requests")
    blood_request = coll.find({"_id": ObjectId(blood_request_id)}).next()
    blood_request["_id"] = str(blood_request["_id"])
    return JsonResponse(data=blood_request, status=200)


@api_view(['PUT'])
def user_blood_request_details_update(request, blood_request_id):
    try:
        email = get_jwt_identity(request)
        if not email:
            return HttpResponse(content="user not logged in", status=401)
    except InvalidRequest:
        return HttpResponse(content="user not logged in", status=401)

    client = _get_db()
    coll = client.get_collection("blood_requests")
    data = json.loads(request.body)
    coll.update_one(
        filter={"_id": ObjectId(blood_request_id)}, upsert=True,
        update={"$set": data}
    )
    return HttpResponse(status=200)


@api_view(['PATCH'])
def user_decrease_blood_request_unit(request):
    try:
        email = get_jwt_identity(request)
        if not email:
            return HttpResponse(content="user not logged in", status=401)
    except InvalidRequest:
        return HttpResponse(content="user not logged in", status=401)

    client = _get_db()
    coll = client.get_collection("blood_requests")
    data = json.loads(request.body)
    blood_request = coll.find({"_id": ObjectId(data["blood_request_id"])}).next()
    unit = blood_request["unit"]
    if unit == 1:
        return HttpResponse(content="cannot decrease, please delete", status=409)

    coll.update_one(
        filter={"_id": ObjectId(data["blood_request_id"])}, upsert=True,
        update={'$inc': {'unit': -1}}
    )
    unit -= 1
    return JsonResponse(data={"unit": unit}, status=200)


@api_view(['PATCH'])
def user_increase_blood_request_unit(request):
    try:
        email = get_jwt_identity(request)
        if not email:
            return HttpResponse(content="user not logged in", status=401)
    except InvalidRequest:
        return HttpResponse(content="user not logged in", status=401)

    client = _get_db()
    coll = client.get_collection("blood_requests")
    data = json.loads(request.body)
    blood_request = coll.find({"_id": ObjectId(data["blood_request_id"])}).next()
    unit = blood_request["unit"]
    coll.update_one(
        filter={"_id": ObjectId(data["blood_request_id"])}, upsert=True,
        update={'$inc': {'unit': 1}}
    )
    unit += 1
    return JsonResponse(data={"unit": unit}, status=200)


@api_view(['DELETE'])
def user_blood_request_details_delete(request, blood_request_id):
    try:
        email = get_jwt_identity(request)
        if not email:
            return HttpResponse(content="user not logged in", status=401)
    except InvalidRequest:
        return HttpResponse(content="user not logged in", status=401)

    client = _get_db()
    coll = client.get_collection("blood_requests")
    coll.delete_one({'_id': ObjectId(blood_request_id)})
    return HttpResponse(status=200)


# USER PAGE END
# BLOOD REQUESTS PAGE START


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
                "blood_group": blood_request["blood_group"],
                "city": blood_request["city"],
                "district": blood_request["district"],
                "phone": blood_request["phone"],
                "email": blood_request["email"],
                "unit": blood_request["unit"]
            }
        )
    return JsonResponse(data=blood_requests_resp, status=200, safe=False)


@api_view(['GET'])
def get_blood_request_details(request, blood_request_id):
    client = _get_db()
    coll = client.get_collection("blood_requests")
    blood_request = coll.find({"_id": ObjectId(blood_request_id)}).next()
    blood_request["_id"] = str(blood_request["_id"])
    return JsonResponse(data=blood_request, status=200)


@api_view(['GET'])
def get_validation_questions(request, blood_request_id):
    client = _get_db()
    coll = client.get_collection("blood_requests")
    blood_request = coll.find({"_id": ObjectId(blood_request_id)}).next()
    blood_product_type = blood_request["blood_product_type"]
    coll = client.get_collection("validation")
    validation = coll.find({"blood_product_type": blood_product_type}).next()
    questions = {}
    print(validation)
    for key, val in validation.items():
        if key.startswith("question_"):
            questions[key] = val

    return JsonResponse(data=questions, status=200)


@api_view(['POST'])
def validate_donation(request, blood_request_id):
    client = _get_db()
    data = json.loads(request.body)
    coll = client.get_collection("blood_requests")
    blood_request = coll.find({"_id": ObjectId(blood_request_id)}).next()
    blood_product_type = blood_request["blood_product_type"]
    coll = client.get_collection("validation")
    validation = coll.find({"blood_product_type": blood_product_type}).next()
    questions_answers = {}
    for key, val in validation.items():
        if key.startswith("question_") or key.startswith("answer_"):
            questions_answers[key] = val

    if questions_answers != data:
        return HttpResponse(content="donor not fit requirements", status=409)

    return HttpResponse(status=200)


@api_view(['POST'])
def donate_to_blood_request(request, blood_request_id):
    client = _get_db()
    coll = client.get_collection("blood_requests")
    blood_request = coll.find({"_id": ObjectId(blood_request_id)}).next()
    data = json.loads(request.body)
    mail_body = f"""
        <html>
          <head>
            <meta charset="UTF-8">
          </head>
          <body>
            <h1>Contact Information for {data['name']} {data['surname']}</h1>
            <p><strong>Address:</strong> {data['address']}</p>
            <p><strong>Phone:</strong> {data['phone']}</p>
            <p><strong>Email:</strong> {data['email']}</p>
          </body>
        </html>
    """
    send_mail(
        to_whom=blood_request["email_address"],
        subject="Donor Found!!!", body=mail_body
    )

    return HttpResponse(status=200)

# BLOOD REQUESTS PAGE END

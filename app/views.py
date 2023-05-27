from typing import List, Union
from functools import lru_cache
import certifi
from bson.json_util import dumps
from bson import ObjectId
import json

from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

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


def loginPage(request):
    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        user_document = _get_db().get_collection("users").find({"email": email})
        if user_document is not None:
            real_password = user_document.next()["password"]
            if real_password == password:
                response = JsonResponse( data={"message": "Log in successful. Redirecting main page..."}, status=200)
            else:
                response = JsonResponse(
                    data={"message": "Password is wrong."}, status=200
                )
        else:
            response = JsonResponse(data={"message": "E-mail is invalid."}, status=200)
        return response

def register_user(request):
    from django.utils.dateparse import parse_date
    if request.method == 'POST':
        email = request.POST.get('email').lower()
        all_users = _get_db().get_collection("users")
        user_document = all_users.find({"email": email})
        if user_document is not None:
            response = JsonResponse(
                    data={"message": "E-mail is already registered Try login."}, status=200
                )
            return response
        password_org = request.POST.get('password_org')
        password_repeat = request.POST.get('password_repeat')
        if password_org != password_repeat:
            response = JsonResponse(
                    data={"message": "Passwords do not match."}, status=200
                )
            return response
        def str_to_bool(s):
            if s == 'True':
                return True
            elif s == 'False':
                return False
            else:
                raise ValueError  # evil ValueError that doesn't tell you what the wrong value was
        name = request.POST.get('name')
        surname = request.POST.get('surname')
        date_of_birth = parse_date(request.POST.get('date_of_birth')) ##date = datetime(1996, 2, 1)
        blood_group = request.POST.get('blood_group')
        phone = int(request.POST.get('phone'))

        city = request.POST.get('city')
        county = request.POST.get('county')
        street = request.POST.get('street')
        zip_code = int( request.POST.get('zip_code'))
        address = request.POST.get('address')
        nearby_email = str_to_bool(request.POST.get('nearby_email'))
        nearby_message = str_to_bool(request.POST.get('nearby_message'))
        donation_warning = str_to_bool(request.POST.get('donation_warning'))

        new_preference = {
            "nearby_email": nearby_email,
            "nearby_message": nearby_message,
            "donation_warning": donation_warning
        }
        all_preferences = _get_db().get_collection("preferences")
        pref_doc = all_preferences.insert_one(new_preference)



        new_user = {
            "name": name,
            "surname": surname,
            "date_of_birth": date_of_birth,
            "blood_group": blood_group,
            "phone": phone,
            "email": email,
            "password": password_org,
            "city": city,
            "county": county,
            "street": street,
            "zip_code": zip_code,
            "address": address,
            "preference_id": pref_doc.get["_id"].__str__()

        }
        all_users.insert_one(new_user)

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
                "contact_gsm": blood_request["contact_gsm"],
                "email_address": blood_request["email_address"],
                "blood_group": blood_request["blood_group"] if "blood_group" in blood_request else ""
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


@api_view(['POST'])
def add_blood_request(request):
    client = _get_db()
    collection = client['blood_requests']
    data = json.loads(request.body)
    collection.insert_one(data)
    return HttpResponse(status=200)


@api_view(['DELETE'])
def delete_blood_request(request, object_id):
    client = _get_db()
    collection = client['blood_requests']
    collection.delete_one({'_id': ObjectId(object_id)})
    return HttpResponse(status=200)


@api_view(['GET'])
def donate_to_blood_request(request, blood_request_id):
    client = _get_db()
    coll = client.get_collection("blood_requests")
    blood_request = coll.find({"_id": ObjectId(blood_request_id)}).next()
    blood_product_type = blood_request["blood_product_type"]
    coll = client.get_collection("validation_forms")
    validation_form = coll.find({"blood_product_type": blood_product_type}).next()
    validation_form["_id"] = str(validation_form["_id"])
    return JsonResponse(data=validation_form, status=200)


@api_view(['GET', 'POST'])
def validate_to_blood_request(request, blood_request_id):
    client = _get_db()
    coll = client.get_collection("blood_requests")
    blood_request = coll.find({"_id": ObjectId(blood_request_id)}).next()
    blood_product_type = blood_request["blood_product_type"]
    coll = client.get_collection("validation_forms")
    validation_form = coll.find({"blood_product_type": blood_product_type}).next()
    request_body = request.body
    if validation_form == request["validation_form"]:
        response = JsonResponse(
            data={"message": "donor fit requirements"}, status=200
        )
        mail_body = f"""
            <html>
              <head>
                <meta charset="UTF-8">
              </head>
              <body>
                <h1>Contact Information for {request_body['name']} {request_body['surname']}</h1>
                <p><strong>Address:</strong> {request_body['address']}</p>
                <p><strong>Phone:</strong> {request_body['gsm']}</p>
                <p><strong>Email:</strong> {request_body['email']}</p>
              </body>
            </html>
        """
        send_mail(
            to_whom=blood_request["email_address"],
            subject="Donor Found!!!", body=mail_body
        )
    else:
        response = JsonResponse(
            data={"message": "donor does not fit requirements"}, status=200
        )

    return response


@api_view(['POST'])
def donate_to_blood_request_draft(request, blood_request_id):
    client = _get_db()
    coll = client.get_collection("blood_requests")
    blood_request = coll.find({"_id": ObjectId(blood_request_id)}).next()
    request_body = json.loads(request.body)
    print(request_body);
    mail_body = f"""
        <html>
          <head>
            <meta charset="UTF-8">
          </head>
          <body>
            <h1>Contact Information for {request_body['name']} {request_body['surname']}</h1>
            <p><strong>Address:</strong> {request_body['address']}</p>
            <p><strong>Phone:</strong> {request_body['gsm']}</p>
            <p><strong>Email:</strong> {request_body['email_address']}</p>
          </body>
        </html>
    """
    send_mail(
        to_whom=blood_request["email_address"],
        subject="Donor Found!!!", body=mail_body
    )

    return HttpResponse(status=200)

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login

import json

from utils import parseCSVFileFromDjangoFile, isNumber, returnTestChartData
from getInsight import parseAuthorCSVFile, getReviewScoreInfo, getAuthorInfo, getReviewInfo, getSubmissionInfo
from models import Member
from models import MemberFileData

# Create your views here.
# Note: a view is a func taking the HTTP request and returns sth accordingly
from rest_framework.decorators import api_view

def public(request):
    return HttpResponse("You don't need to be authenticated to see this")

@api_view(['GET'])
def private(request):
    return HttpResponse("You should not see this message if not authenticated!")

def index(request):
	return HttpResponse("Hello, world. You're at the polls index.")

def test(request):
	return HttpResponse("<h1>This is the very first HTTP request!</h1>")

@csrf_exempt
def login(request):
    print "Checking if user is able to log in"
    print request.POST
    print request.content_type
    mem = Member.objects.filter(username=request.POST['username'], password=request.POST['password'])
    if mem.exists():
        print "user logged in"
        data = {
            "logged": "true"
        }
        return HttpResponse(json.dumps(data))
    else:
        print "access denied"
        data = {
            "logged": "false"
        }
        return HttpResponse(json.dumps(data))
    #user = authenticate(request, username=username, password=password)
    #if user is not None:
    #    login(request,user)
    #    return HttpResponse("Logged in")
    #else:
    #    return HttpResponse("Failed to log in")
#add in register method


#add in retrieve-data method (subjected to user)
@csrf_exempt
def saveData(request):
    print "Inside save data function"
    #save data to model
    x = MemberFileData("user1", request.body)
    x.save()
    print "Data saved in database"
    data = {
        "saved": "true"
    }
    return HttpResponse(json.dumps(data))

# Note: csr: cross site request, adding this to enable request from localhost
@csrf_exempt
def uploadCSV(request):
	print "Inside the upload function"
	if request.FILES:
		csvFile = request.FILES['file']
		fileName = str(csvFile.name)
		rowContent = ""

		if "author.csv" in fileName:
			rowContent = getAuthorInfo(csvFile)
		elif "score.csv" in fileName:
			rowContent = getReviewScoreInfo(csvFile)
		elif "review.csv" in fileName:
			rowContent = getReviewInfo(csvFile)
		elif "submission.csv" in fileName:
			rowContent = getSubmissionInfo(csvFile)
		else:
			rowContent = returnTestChartData(csvFile)

		print type(csvFile.name)

		if request.POST:
	# current problem: request from axios not recognized as POST
			# csvFile = request.FILES['file']
			print "Now we got the csv file"

		return HttpResponse(json.dumps(rowContent))
		# return HttpResponse("Got the CSV file.")
	else:
		print "Not found the file!"
		return HttpResponseNotFound('Page not found for CSV')

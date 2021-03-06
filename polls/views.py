# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt

import json

from utils import parseCSVFileFromDjangoFile, isNumber, returnTestChartData
from getInsight import getInfo, avgScorePerCountry, acceptedPerCountry, rejectedPerCountry, avgScorePerOrganisation, rejectedPerOrganisation, acceptedPerOrganisation, acceptedAvgScorePerCountry, acceptedAvgScorePerOrg

# Create your views here.
# Note: a view is a func taking the HTTP request and returns sth accordingly

def index(request):
	return HttpResponse("Hello, world. You're at the polls index.")

def test(request):
	return HttpResponse("<h1>This is the very first HTTP request!</h1>")

# Note: csr: cross site request, adding this to enable request from localhost
@csrf_exempt
def uploadCSV(request):
	print "Inside the upload function"
	if request.FILES:
		count = request.POST['count']
		csvIfMultiple = "false"

		if count > 1:
			csvIfMultiple = "true"

		rowContent = ""
		fullRowContent = {"infoData" : {}}

		for i in range(int(count)):
			csvFile = request.FILES["file"+str((i+1))]
			rowContent = getInfo(csvFile, csvIfMultiple)
			fullRowContent["infoData"].update(rowContent["infoData"])

		if count > 1:
			innerMap = fullRowContent["infoData"]

			# avg score per country
			if "authCountMap" in innerMap and "IDReviewMap" in innerMap:
				rowContent = avgScorePerCountry(innerMap["authCountMap"], innerMap["IDReviewMap"])
				fullRowContent["infoData"].update(rowContent["infoData"])

			# avg score per org
			if "authOrgMap" in innerMap and "IDReviewMap" in innerMap:
				rowContent = avgScorePerOrganisation(innerMap["authOrgMap"], innerMap["IDReviewMap"])
				fullRowContent["infoData"].update(rowContent["infoData"])

			# no accepted per country
			if "subAcceptMap" in innerMap and "authCountMap" in innerMap:
				rowContent = acceptedPerCountry(innerMap["subAcceptMap"], innerMap["authCountMap"])
				fullRowContent["infoData"].update(rowContent["infoData"])

			# no reject per country
			if "subRejectMap" in innerMap and "authCountMap" in innerMap:
				rowContent = rejectedPerCountry(innerMap["subRejectMap"], innerMap["authCountMap"])
				fullRowContent["infoData"].update(rowContent["infoData"])

			# no accepted per org
			if "subAcceptMap" in innerMap and "authOrgMap" in innerMap:
				rowContent = acceptedPerOrganisation(innerMap["subAcceptMap"], innerMap["authOrgMap"])
				fullRowContent["infoData"].update(rowContent["infoData"])
			
			# no rejected per org
			if "subRejectMap" in innerMap and "authOrgMap" in innerMap:
				rowContent = rejectedPerOrganisation(innerMap["subRejectMap"], innerMap["authOrgMap"])
				fullRowContent["infoData"].update(rowContent["infoData"])
			
			# accepted average scores per org
			if "subAcceptMap" in innerMap and "authOrgMap" in innerMap and "IDReviewMap" in innerMap:
				rowContent = acceptedAvgScorePerOrg(innerMap["subAcceptMap"], innerMap["authOrgMap"], innerMap["IDReviewMap"])
				fullRowContent["infoData"].update(rowContent["infoData"])

			# accepted average scores per country
			if "subAcceptMap" in innerMap and "authCountMap" in innerMap and "IDReviewMap" in innerMap:
				rowContent = acceptedAvgScorePerCountry(innerMap["subRejectMap"], innerMap["authCountMap"], innerMap["IDReviewMap"])
				fullRowContent["infoData"].update(rowContent["infoData"])

		print type(csvFile.name)
		
		if request.POST:
	# current problem: request from axios not recognized as POST
			# csvFile = request.FILES['file']
			print "Now we got the csv file"

		return HttpResponse(json.dumps(fullRowContent))
		# return HttpResponse("Got the CSV file.")
	else:
		print "Not found the file!"
		return HttpResponseNotFound('Page not found for CSV')
import csv
import codecs
from collections import Counter

from utils import parseCSVFile, testCSVFileFormatMatching, isNumber, parseSubmissionTime

def getInfo(inputFile):

	parsedResult = {}
	columnHeaders = {}
	submissionID = {}

	lines = parseCSVFile(inputFile)
	columnHeaders = [x for x in lines][0]
	lines = lines[1:]

	# submission number: all these information should have corresponding submission number..
	if "nosub" in columnHeaders:
		columnIndex = columnHeaders.index('nosub')
		submissionIDs = set([str(line[columnIndex]) for line in lines])

		# author first and last name
		if "firstauth" in columnHeaders and "lastauth" in columnHeaders:
			columnIndexFirst = columnHeaders.index('firstauth')
			columnIndexSecond = columnHeaders.index('lastauth')

			parsedResult['topAuthors'] = getAuth(lines, columnIndexFirst, columnIndexSecond)

		# author country
		if "countauth" in columnHeaders:
			columnIndex = columnHeaders.index('countauth')
			
			parsedResult['topCountries'] = getCountry(lines, columnIndex)

		# author organization
		if "orgauth" in columnHeaders:
			columnIndex = columnHeaders.index('orgauth')

			parsedResult['topAffiliations'] = getAffliation(lines, columnIndex)

		# Doesn't use any information, will be here.
		scoreDistributionCounts = [0] * int((3 + 3) / 0.25)
		recommendDistributionCounts = [0] * int((1 - 0) / 0.1)

		scoreDistributionLabels = [" ~ "] * len(scoreDistributionCounts)
		recommendDistributionLabels = [" ~ "] * len(recommendDistributionCounts)

		for index, col in enumerate(scoreDistributionCounts):
			scoreDistributionLabels[index] = str(-3 + 0.25 * index) + " ~ " + str(-3 + 0.25 * index + 0.25)

		for index, col in enumerate(recommendDistributionCounts):
			recommendDistributionLabels[index] = str(0 + 0.1 * index) + " ~ " + str(0 + 0.1 * index + 0.1)

		# review evaluation based on submission number
		if "evarev" in columnHeaders:
			columnIndexFirst = columnHeaders.index('nosub')
			columnIndexSecond = columnHeaders.index('evarev')
			submissionIDReviewMap = {}

			scoreList = []
			recommendList = []
			confidenceList = []
			
			for submissionID in submissionIDs:
				reviews = [str(line[columnIndexSecond]).replace("\r", "") for line in lines if str(line[columnIndexFirst]) == submissionID]
				confidences = [float(review.split("\n")[1].split(": ")[1]) for review in reviews]
				scores = [float(review.split("\n")[0].split(": ")[1]) for review in reviews]

				confidenceList.append(sum(confidences) / len(confidences))

				try:
					recommends = map(lambda review: 1.0 if review.split("\n")[2].split(": ")[1] == "yes" else 0.0, reviews)
				except:
					recommends = [0.0 for n in range(len(reviews))]

				weightedScore = sum(x * y for x, y in zip(scores, confidences)) / sum(confidences)
				weightedRecommend = sum(x * y for x, y in zip(recommends, confidences)) / sum(confidences)

				scoreColumn = min(int((weightedScore + 3) / 0.25), 23)
				recommendColumn = min(int((weightedRecommend) / 0.1), 9)
				scoreDistributionCounts[scoreColumn] += 1
				recommendDistributionCounts[recommendColumn] += 1
				submissionIDReviewMap[submissionID] = {'score': weightedScore, 'recommend': weightedRecommend}

				scoreList.append(weightedScore)
				recommendList.append(weightedRecommend)

			parsedResult['IDReviewMap'] = submissionIDReviewMap
			parsedResult['scoreList'] = scoreList
			parsedResult['recommendList'] = recommendList
			
			parsedResult['meanScore'] = sum(scoreList) / len(scoreList)
			parsedResult['meanRecommend'] = sum(recommendList) / len(recommendList)
			parsedResult['meanConfidence'] = sum(confidenceList) / len(confidenceList)

			parsedResult['scoreDistribution'] = {'labels': scoreDistributionLabels, 'counts': scoreDistributionCounts}
			parsedResult['recommendDistribution'] = {'labels': recommendDistributionLabels, 'counts': recommendDistributionCounts}

		# time of submission
		if "timesub" in columnHeaders:
			columnIndex = columnHeaders.index("timesub")
			submissionTimes = [parseSubmissionTime(str(ele[columnIndex])) for ele in lines]
			submissionTimes = Counter(submissionTimes)
			timeStamps = sorted([k for k in submissionTimes])
			submittedNumber = [0 for n in range(len(timeStamps))]
			timeSeries = []

			for index, timeStamp in enumerate(timeStamps):
				if index == 0:
					submittedNumber[index] = submissionTimes[timeStamp]
				else:
					submittedNumber[index] = submissionTimes[timeStamp] + submittedNumber[index - 1]

				timeSeries.append({'x': timeStamp, 'y': submittedNumber[index]})
			
			parsedResult['timeSeries'] = timeSeries

		# time of last updated submission
		if "timeupsub" in columnHeaders:
			columnIndex = columnHeaders.index("timeupsub")
			lastEditTimes = [parseSubmissionTime(str(ele[columnIndex])) for ele in lines]
			lastEditTimes = Counter(lastEditTimes)
			lastEditStamps = sorted([k for k in lastEditTimes])
			lastEditNumber = [0 for n in range(len(lastEditStamps))]
			lastEditSeries = []

			for index, lastEditStamp in enumerate(lastEditStamps):
				if index == 0:
					lastEditNumber[index] = lastEditTimes[lastEditStamp]
				else:
					lastEditNumber[index] = lastEditTimes[lastEditStamp] + lastEditNumber[index - 1]

				lastEditSeries.append({'x': lastEditStamp, 'y': lastEditNumber[index]})

			parsedResult['lastEditSeries'] = lastEditSeries

		acceptedSubmission = {}
		rejectedSubmission = {}

		# accepted or rejected submission
		if "arsub" in columnHeaders:
			columnIndex = columnHeaders.index("arsub")

			acceptedSubmission = [line for line in lines if str(line[columnIndex]) == 'accept']
			rejectedSubmission = [line for line in lines if str(line[columnIndex]) == 'reject']

			acceptanceRate = float(len(acceptedSubmission)) / len(lines)

			parsedResult['acceptanceRate'] = acceptanceRate

			# author of submission
			if "authsub" in columnHeaders:
				columnIndex = columnHeaders.index("authsub")
				
				acceptedAuthors = [str(ele[columnIndex]).replace(" and ", ", ").split(", ") for ele in acceptedSubmission]
				acceptedAuthors = [ele for item in acceptedAuthors for ele in item]

				topAcceptedAuthors = Counter(acceptedAuthors).most_common(10)
				topAcceptedAuthorsMap = {'names': [ele[0] for ele in topAcceptedAuthors], 'counts': [ele[1] for ele in topAcceptedAuthors]}

				parsedResult['topAcceptedAuthors'] = topAcceptedAuthorsMap

		# keywords in submission
		if "keysub" in columnHeaders:
			columnIndex = columnHeaders.index("keysub")
			
			allKeywords = [str(ele[columnIndex]).lower().replace("\r", "").split("\n") for ele in lines]
			allKeywords = [ele for item in allKeywords for ele in item]
			allKeywordMap = {k : v for k, v in Counter(allKeywords).iteritems()}
			allKeywordList = [[ele[0], ele[1]] for ele in Counter(allKeywords).most_common(20)]

			parsedResult['overallKeywordMap'] = allKeywordMap
			parsedResult['overallKeywordList'] = allKeywordList

			# accepted or rejected submission
			if "arsub" in columnHeaders:
				acceptedKeywords = [str(ele[columnIndex]).lower().replace("\r", "").split("\n") for ele in acceptedSubmission]
				acceptedKeywords = [ele for item in acceptedKeywords for ele in item]
				acceptedKeywordMap = {k : v for k, v in Counter(acceptedKeywords).iteritems()}
				acceptedKeywordList = [[ele[0], ele[1]] for ele in Counter(acceptedKeywords).most_common(20)]

				parsedResult['acceptedKeywordMap'] = acceptedKeywordMap
				parsedResult['acceptedKeywordList'] = acceptedKeywordList

				rejectedKeywords = [str(ele[columnIndex]).lower().replace("\r", "").split("\n") for ele in rejectedSubmission]
				rejectedKeywords = [ele for item in rejectedKeywords for ele in item]
				rejectedKeywordMap = {k : v for k, v in Counter(rejectedKeywords).iteritems()}
				rejectedKeywordList = [[ele[0], ele[1]] for ele in Counter(rejectedKeywords).most_common(20)]

				parsedResult['rejectedKeywordMap'] = rejectedKeywordMap
				parsedResult['rejectedKeywordList'] = rejectedKeywordList

		# track number of submission
		if "tracknosub" in columnHeaders:
			tracks = {}
			paperGroupsByTrack = {}
			keywordsGroupByTrack = {}
			acceptanceRateByTrack = {}
			comparableAcceptanceRate = {}
			topAuthorsByTrack = {}

			columnIndex = columnHeaders.index("tracknamesub")
			tracks = set([str(ele[columnIndex]) for ele in lines])
			paperGroupsByTrack = {track : [line for line in lines if str(line[columnIndex]) == track] for track in tracks}

			# Obtained from the JCDL.org website: past conferences
			comparableAcceptanceRate['year'] = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018]
			comparableAcceptanceRate['Full Papers'] = [0.29, 0.28, 0.27, 0.29, 0.29, 0.30, 0.29, 0.30]
			comparableAcceptanceRate['Short Papers'] = [0.29, 0.37, 0.31, 0.31, 0.32, 0.50, 0.35, 0.32]
			
			for track, papers in paperGroupsByTrack.iteritems():
				# keyword of submission
				if "keysub" in columnHeaders:
					columnIndex = columnHeaders.index("keysub")

					keywords = [str(ele[columnIndex]).lower().replace("\r", "").split("\n") for ele in papers]
					keywords = [ele for item in keywords for ele in item]
					keywordMap = [[ele[0], ele[1]] for ele in Counter(keywords).most_common(20)]
					keywordsGroupByTrack[track] = keywordMap

				acceptedPapersThisTrack = {}

				if "arsub" in columnHeaders:
					columnIndex = columnHeaders.index("arsub")

					acceptedPapersPerTrack = [ele for ele in papers if str(ele[columnIndex]) == 'accept']
					acceptanceRateByTrack[track] = float(len(acceptedPapersPerTrack)) / len(papers)
					acceptedPapersThisTrack = [paper for paper in papers if str(paper[columnIndex]) == 'accept']

				if "authsub" in columnHeaders:
					columnIndex = columnHeaders.index("authsub")

					acceptedAuthorsThisTrack = [str(ele[columnIndex]).replace(" and ", ", ").split(", ") for ele in acceptedPapersThisTrack]
					acceptedAuthorsThisTrack = [ele for item in acceptedAuthorsThisTrack for ele in item]

					topAcceptedAuthorsThisTrack = Counter(acceptedAuthorsThisTrack).most_common(10)
					topAuthorsByTrack[track] = {'names': [ele[0] for ele in topAcceptedAuthorsThisTrack], 'counts': [ele[1] for ele in topAcceptedAuthorsThisTrack]}

				if track == "Full Papers" or track == "Short Papers":
					comparableAcceptanceRate[track].append(float(len(acceptedPapersPerTrack)) / len(papers))

			if "keysub" in columnHeaders:
				parsedResult['keywordsByTrack'] = keywordsGroupByTrack

			if "arsub" in columnHeaders:
				parsedResult['acceptanceRateByTrack'] = acceptanceRateByTrack

			if "authsub" in columnHeaders:
				parsedResult['topAuthorsByTrack'] = topAuthorsByTrack

			parsedResult['comparableAcceptanceRate'] = comparableAcceptanceRate

			# A list of labels for by track
			acceptanceRateByTrackLabels = ['Tutorials', 'Short Papers', 'JCDL 2018 - Workshops', 'Full Papers', 'Poster/Demo', 'Panels', 'Doctoral Consortium', 'Posters and Demos']
			topAuthorsByTrackLabels = ['Tutorials', 'Short Papers', 'JCDL 2018 - Workshops', 'Full Papers', 'Poster/Demo 2', 'Panels', 'Doctoral and Consortium', 'Posters and Demos']
			keywordsByTrackLabels = ['Full Papers', 'Doctoral Consortium', 'Short Papers', 'Posters and Demos', 'Tutorials', 'JCDL 2018 - Workshops', 'Poster/Demo 2', 'Panels']

			parsedResult['acceptanceRateByTrackLabels'] = {'labels': acceptanceRateByTrackLabels}
			parsedResult['topAuthorsByTrackLabels'] = {'labels': topAuthorsByTrackLabels}
			parsedResult['keywordsByTrackLabels'] = {'labels': keywordsByTrackLabels}

	# although norev not used, does it make sense to not have 1 - for reviewScore
	if "norev" in columnHeaders:
		# number of review, type of field of review, score
		if "fieldtyperev" in columnHeaders and "typescorerev" in columnHeaders:
			columnIndexFirst = columnHeaders.index("norev")
			columnIndexSecond = columnHeaders.index("fieldtyperev")
			columnIndexThird = columnHeaders.index("typescorerev")

			scores = []
			confidences = []
			isRecommended = []

			scores = [int(line[columnIndexThird]) for line in lines if int(line[columnIndexSecond]) == 1]
			confidences = [int(line[columnIndexThird]) for line in lines if int(line[columnIndexSecond]) == 2]
			isRecommended = [str(line[columnIndexThird]).replace("\r", "") for line in lines if int(line[columnIndexSecond]) == 3]

			parsedResult['yesPercentage'] = float(isRecommended.count('yes')) / len(isRecommended)
			parsedResult['meanScore'] = sum(scores) / float(len(scores))
			parsedResult['meanConfidence'] = sum(confidences) / float(len(confidences))
			parsedResult['totalReview'] = len(confidences)

	return {'infoData': parsedResult}

def getAuth(lines, columnIndexFirst, columnIndexSecond):
	authorList = []

	for authorInfo in lines:
		authorList.append({'name': authorInfo[columnIndexFirst] + " " + authorInfo[columnIndexSecond]})
	
	authors = [ele['name'] for ele in authorList if ele] # adding in the if ele in case of empty strings; same applies below
	topAuthors = Counter(authors).most_common(10)

	return {'labels': [ele[0] for ele in topAuthors], 'data': [ele[1] for ele in topAuthors]}

def getCountry(lines, columnIndex):
	countryList = []

	for countryInfo in lines:
		countryList.append({'country': countryInfo[columnIndex]})

	countries = [ele['country'] for ele in countryList if ele]
	topCountries = Counter(countries).most_common(10)

	return  {'labels': [ele[0] for ele in topCountries], 'data': [ele[1] for ele in topCountries]}

def getAffliation(lines, columnIndex):
	affliationList = []

	for affliationInfo in lines:
		affliationList.append({'affliation': affliationInfo[columnIndex]})
	
	affiliations = [ele['affliation'] for ele in affliationList if ele]
	topAffiliations = Counter(affiliations).most_common(10)

	return {'labels': [ele[0] for ele in topAffiliations], 'data': [ele[1] for ele in topAffiliations]}

if __name__ == "__main__":
	parseCSVFile(fileName)
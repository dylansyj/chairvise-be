import csv
import codecs
from collections import Counter

from utils import parseCSVFile, testCSVFileFormatMatching, isNumber, parseSubmissionTime

#activate sesssions
from importlib import import_module
from django.conf import settings
SessionStore = import_module(settings.SESSION_ENGINE).SessionStore
s = SessionStore()

def parseAuthorCSVFile(inputFile):

	csvFile = inputFile
	dialect = csv.Sniffer().sniff(codecs.EncodedFile(csvFile, "utf-8").read(1024))
	csvFile.open()
	# reader = csv.reader(codecs.EncodedFile(csvFile, "utf-8"), delimiter=',', dialect=dialect)
	reader = csv.reader(codecs.EncodedFile(csvFile, "utf-8"), delimiter=',', dialect='excel')

	rowResults = []
	for index, row in enumerate(reader):
		rowResults.append(row)
		print row
		print type(row)
		if index == 5:
			break

	parsedResult = {}

	return parsedResult

def getAuthorInfo(inputFile):
	"""
	author.csv: header row, author names with affiliations, countries, emails
	data format:
	submission ID | f name | s name | email | country | affiliation | page | person ID | corresponding?
	"""
	parsedResult = {}

	lines = parseCSVFile(inputFile)[1:]
	lines = [ele for ele in lines if ele]

	# store in session
	s['authorLines'] = lines;

	authorList = []
	for authorInfo in lines:
		# authorInfo = line.replace("\"", "").split(",")
		# print authorInfo
		authorList.append({'name': authorInfo[1] + " " + authorInfo[2], 'country': authorInfo[4], 'affiliation': authorInfo[5]})
	

	authors = [ele['name'] for ele in authorList if ele] # adding in the if ele in case of empty strings; same applies below
	topAuthors = Counter(authors).most_common(10)
	parsedResult['topAuthors'] = {'labels': [ele[0] for ele in topAuthors], 'data': [ele[1] for ele in topAuthors]}

	countries = [ele['country'] for ele in authorList if ele]
	topCountries = Counter(countries).most_common(10)
	parsedResult['topCountries'] = {'labels': [ele[0] for ele in topCountries], 'data': [ele[1] for ele in topCountries]}

	affiliations = [ele['affiliation'] for ele in authorList if ele]
	topAffiliations = Counter(affiliations).most_common(10)
	parsedResult['topAffiliations'] = {'labels': [ele[0] for ele in topAffiliations], 'data': [ele[1] for ele in topAffiliations]}

	return {'infoType': 'author', 'infoData': parsedResult}

def getReviewScoreInfo(inputFile):
	"""
	review_score.csv
	data format:
	review ID | field ID | score
	File has header

	e.g. 1,1,3 - score (can be negative)
	     1,2,5 - confidence
	     1,3,no - recommended
	"""
	parsedResult = {}
	lines = parseCSVFile(inputFile)[1:]
	lines = [ele for ele in lines if ele]
	scores = []
	confidences = []
	isRecommended = []

	scores = [int(line[2]) for line in lines if int(line[1]) == 1]
	confidences = [int(line[2]) for line in lines if int(line[1]) == 2]
	isRecommended = [str(line[2]).replace("\r", "") for line in lines if int(line[1]) == 3]

	parsedResult['yesPercentage'] = float(isRecommended.count('yes')) / len(isRecommended)
	parsedResult['meanScore'] = sum(scores) / float(len(scores))
	parsedResult['meanConfidence'] = sum(confidences) / float(len(confidences))
	parsedResult['totalReview'] = len(confidences)

	return {'infoType': 'reviewScore', 'infoData': parsedResult}

def getReviewInfo(inputFile):
	"""
	review.csv
	data format: 
	review ID | paper ID? | reviewer ID | reviewer name | unknown | text | scores | overall score | unknown | unknown | unknown | unknown | date | time | recommend?
	File has NO header

	score calculation principles:
	Weighted Average of the scores, using reviewer's confidence as the weights

	recommended principles:
	Yes: 1; No: 0; weighted average of the 1 and 0's, also using reviewer's confidence as the weights
	"""
	parsedResult = {}
	lines = parseCSVFile(inputFile)
	lines = [ele for ele in lines if ele]
	s['reviewLines'] = lines
	evaluation = [str(line[6]).replace("\r", "") for line in lines]
	submissionIDs = set([str(line[1]) for line in lines])

	scoreList = []
	recommendList = []
	confidenceList = []

	submissionIDReviewMap = {}

	# Idea: from -3 to 3 (min to max scores possible), every 0.25 will be a gap
	scoreDistributionCounts = [0] * int((3 + 3) / 0.25)
	recommendDistributionCounts = [0] * int((1 - 0) / 0.1)

	scoreDistributionLabels = [" ~ "] * len(scoreDistributionCounts)
	recommendDistributionLabels = [" ~ "] * len(recommendDistributionCounts)

	for index, col in enumerate(scoreDistributionCounts):
		scoreDistributionLabels[index] = str(-3 + 0.25 * index) + " ~ " + str(-3 + 0.25 * index + 0.25)

	for index, col in enumerate(recommendDistributionCounts):
		recommendDistributionLabels[index] = str(0 + 0.1 * index) + " ~ " + str(0 + 0.1 * index + 0.1)

	for submissionID in submissionIDs:
		reviews = [str(line[6]).replace("\r", "") for line in lines if str(line[1]) == submissionID]
		# print reviews
		confidences = [float(review.split("\n")[1].split(": ")[1]) for review in reviews]
		scores = [float(review.split("\n")[0].split(": ")[1]) for review in reviews]

		confidenceList.append(sum(confidences) / len(confidences))
		# recommends = [1.0 for review in reviews if review.split("\n")[2].split(": ")[1] == "yes" else 0.0]
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
	parsedResult['meanScore'] = sum(scoreList) / len(scoreList)
	parsedResult['meanRecommend'] = sum(recommendList) / len(recommendList)
	parsedResult['meanConfidence'] = sum(confidenceList) / len(confidenceList)
	parsedResult['recommendList'] = recommendList
	parsedResult['scoreDistribution'] = {'labels': scoreDistributionLabels, 'counts': scoreDistributionCounts}
	parsedResult['recommendDistribution'] = {'labels': recommendDistributionLabels, 'counts': recommendDistributionCounts}

	return {'infoType': 'review', 'infoData': parsedResult}

def getSubmissionInfo(inputFile):
	"""
	submission.csv
	data format: 
	submission ID | track ID | track name | title | authors | submit time | last update time | form fields | keywords | decision | notified | reviews sent | abstract
	File has header
	"""
	parsedResult = {}
	lines = parseCSVFile(inputFile)[1:]
	lines = [ele for ele in lines if ele]
	s['submissionLines'] = lines
	acceptedSubmission = [line for line in lines if str(line[9]) == 'accept']
	rejectedSubmission = [line for line in lines if str(line[9]) == 'reject']

	acceptanceRate = float(len(acceptedSubmission)) / len(lines)

	submissionTimes = [parseSubmissionTime(str(ele[5])) for ele in lines]
	lastEditTimes = [parseSubmissionTime(str(ele[6])) for ele in lines]
	submissionTimes = Counter(submissionTimes)
	lastEditTimes = Counter(lastEditTimes)
	timeStamps = sorted([k for k in submissionTimes])
	lastEditStamps = sorted([k for k in lastEditTimes])
	submittedNumber = [0 for n in range(len(timeStamps))]
	lastEditNumber = [0 for n in range(len(lastEditStamps))]
	timeSeries = []
	lastEditSeries = []
	for index, timeStamp in enumerate(timeStamps):
		if index == 0:
			submittedNumber[index] = submissionTimes[timeStamp]
		else:
			submittedNumber[index] = submissionTimes[timeStamp] + submittedNumber[index - 1]

		timeSeries.append({'x': timeStamp, 'y': submittedNumber[index]})

	for index, lastEditStamp in enumerate(lastEditStamps):
		if index == 0:
			lastEditNumber[index] = lastEditTimes[lastEditStamp]
		else:
			lastEditNumber[index] = lastEditTimes[lastEditStamp] + lastEditNumber[index - 1]

		lastEditSeries.append({'x': lastEditStamp, 'y': lastEditNumber[index]})

	# timeSeries = {'time': timeStamps, 'number': submittedNumber}
	# lastEditSeries = {'time': lastEditStamps, 'number': lastEditNumber}

	acceptedKeywords = [str(ele[8]).lower().replace("\r", "").split("\n") for ele in acceptedSubmission]
	acceptedKeywords = [ele for item in acceptedKeywords for ele in item]
	acceptedKeywordMap = {k : v for k, v in Counter(acceptedKeywords).iteritems()}
	acceptedKeywordList = [[ele[0], ele[1]] for ele in Counter(acceptedKeywords).most_common(20)]

	rejectedKeywords = [str(ele[8]).lower().replace("\r", "").split("\n") for ele in rejectedSubmission]
	rejectedKeywords = [ele for item in rejectedKeywords for ele in item]
	rejectedKeywordMap = {k : v for k, v in Counter(rejectedKeywords).iteritems()}
	rejectedKeywordList = [[ele[0], ele[1]] for ele in Counter(rejectedKeywords).most_common(20)]

	allKeywords = [str(ele[8]).lower().replace("\r", "").split("\n") for ele in lines]
	allKeywords = [ele for item in allKeywords for ele in item]
	allKeywordMap = {k : v for k, v in Counter(allKeywords).iteritems()}
	allKeywordList = [[ele[0], ele[1]] for ele in Counter(allKeywords).most_common(20)]

	tracks = set([str(ele[2]) for ele in lines])
	paperGroupsByTrack = {track : [line for line in lines if str(line[2]) == track] for track in tracks}
	keywordsGroupByTrack = {}
	acceptanceRateByTrack = {}
	comparableAcceptanceRate = {}
	topAuthorsByTrack = {}

	# Obtained from the JCDL.org website: past conferences
	comparableAcceptanceRate['year'] = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018]
	comparableAcceptanceRate['Full Papers'] = [0.29, 0.28, 0.27, 0.29, 0.29, 0.30, 0.29, 0.30]
	comparableAcceptanceRate['Short Papers'] = [0.29, 0.37, 0.31, 0.31, 0.32, 0.50, 0.35, 0.32]
	for track, papers in paperGroupsByTrack.iteritems():
		keywords = [str(ele[8]).lower().replace("\r", "").split("\n") for ele in papers]
		keywords = [ele for item in keywords for ele in item]
		# keywordMap = {k : v for k, v in Counter(keywords).iteritems()}
		keywordMap = [[ele[0], ele[1]] for ele in Counter(keywords).most_common(20)]
		keywordsGroupByTrack[track] = keywordMap

		acceptedPapersPerTrack = [ele for ele in papers if str(ele[9]) == 'accept']
		acceptanceRateByTrack[track] = float(len(acceptedPapersPerTrack)) / len(papers)

		acceptedPapersThisTrack = [paper for paper in papers if str(paper[9]) == 'accept']
		acceptedAuthorsThisTrack = [str(ele[4]).replace(" and ", ", ").split(", ") for ele in acceptedPapersThisTrack]
		acceptedAuthorsThisTrack = [ele for item in acceptedAuthorsThisTrack for ele in item]
		topAcceptedAuthorsThisTrack = Counter(acceptedAuthorsThisTrack).most_common(10)
		topAuthorsByTrack[track] = {'names': [ele[0] for ele in topAcceptedAuthorsThisTrack], 'counts': [ele[1] for ele in topAcceptedAuthorsThisTrack]}

		if track == "Full Papers" or track == "Short Papers":
			comparableAcceptanceRate[track].append(float(len(acceptedPapersPerTrack)) / len(papers))

	acceptedAuthors = [str(ele[4]).replace(" and ", ", ").split(", ") for ele in acceptedSubmission]
	acceptedAuthors = [ele for item in acceptedAuthors for ele in item]
	topAcceptedAuthors = Counter(acceptedAuthors).most_common(10)
	topAcceptedAuthorsMap = {'names': [ele[0] for ele in topAcceptedAuthors], 'counts': [ele[1] for ele in topAcceptedAuthors]}
	# topAcceptedAuthors = {ele[0] : ele[1] for ele in Counter(acceptedAuthors).most_common(10)}

	parsedResult['acceptanceRate'] = acceptanceRate
	parsedResult['overallKeywordMap'] = allKeywordMap
	parsedResult['overallKeywordList'] = allKeywordList
	parsedResult['acceptedKeywordMap'] = acceptedKeywordMap
	parsedResult['acceptedKeywordList'] = acceptedKeywordList
	parsedResult['rejectedKeywordMap'] = rejectedKeywordMap
	parsedResult['rejectedKeywordList'] = rejectedKeywordList
	parsedResult['keywordsByTrack'] = keywordsGroupByTrack
	parsedResult['acceptanceRateByTrack'] = acceptanceRateByTrack
	parsedResult['topAcceptedAuthors'] = topAcceptedAuthorsMap
	parsedResult['topAuthorsByTrack'] = topAuthorsByTrack
	parsedResult['timeSeries'] = timeSeries
	parsedResult['lastEditSeries'] = lastEditSeries
	parsedResult['comparableAcceptanceRate'] = comparableAcceptanceRate

	return {'infoType': 'submission', 'infoData': parsedResult}

# this method should only be called when all 3 files have been uploaded at least once
def getCrossTableInfo():
	"""
	data formats:
	authorLines - submission ID | f name | s name | email | country | affiliation | page | person ID | corresponding
	submissionLines - submission ID | track ID | track name | title | authors | submit time | last update time | form fields | keywords | decision | notified | reviews sent | abstract
	reviewLines - review ID | paper ID? | reviewer ID | reviewer name | unknown | text | scores | overall score | unknown | unknown | unknown | unknown | date | time | recommend?
	"""
	crossTable = getCrossTable()
	parsedResult = {}

	# get top accepted affiliations
	# extract all accepted affiliations
	affiliations = []
	for row in crossTable.values():
		if row['submission'][9] == 'accept':
			for author in row['author']:
				affiliations.append(author[5])
	topAffiliations = Counter(affiliations).most_common(10)
	parsedResult['topAffiliationsByAcceptance'] = {'labels': [ele[0] for ele in topAffiliations], 'data': [ele[1] for ele in topAffiliations]}

	# get top scoring affiliations
	affiliationsWithAvgScores = {}
	# store affiliation -> [total score, count]
	affiliationsWithScoreAndCount = {}
	for row in crossTable.values():
		totalTabulatedScore = 0
		reviews = row['review']
		numReviews = len(reviews)
		if numReviews > 0:
			for review in reviews:
				# get review avg tabulated score
				confidence = float(review[6].split("\n")[1].split(": ")[1])
				score = float(review[6].split("\n")[0].split(": ")[1])
				totalTabulatedScore += (confidence * score)
			# update each affiliation new total score and count
			authors = row['author']
			for author in authors:
				affi = author[5]
				# update if past affiliations have been recorded
				if affi in affiliationsWithScoreAndCount:
					currAffi = affiliationsWithScoreAndCount[affi]
					newTotal = currAffi[0] + totalTabulatedScore
					newCount = currAffi[1] + numReviews
					affiliationsWithScoreAndCount[affi] = [newTotal, newCount]
				else:
					affiliationsWithScoreAndCount[affi] = [totalTabulatedScore, numReviews]
	# get average scores for each affi
	for affi, values in affiliationsWithScoreAndCount.iteritems():
		avgScore = values[0] / values[1]
		affiliationsWithAvgScores[affi] = avgScore

	# get top 10 affis according to score
	sorted_affi = sorted(affiliationsWithAvgScores.items(), key=lambda (k, v): v, reverse=True)[:10]

	parsedResult['topAffiliationsByScore'] = {'labels': [ele[0] for ele in sorted_affi],
											  'data': [ele[1] for ele in sorted_affi]}

	'''
	parsedResult = {}

	lines = parseCSVFile(inputFile)[1:]
	lines = [ele for ele in lines if ele]

	# store in session
	s['authorLines'] = lines;

	authorList = []
	for authorInfo in lines:
		# authorInfo = line.replace("\"", "").split(",")
		# print authorInfo
		authorList.append({'name': authorInfo[1] + " " + authorInfo[2], 'country': authorInfo[4], 'affiliation': authorInfo[5]})
	

	authors = [ele['name'] for ele in authorList if ele] # adding in the if ele in case of empty strings; same applies below
	topAuthors = Counter(authors).most_common(10)
	parsedResult['topAuthors'] = {'labels': [ele[0] for ele in topAuthors], 'data': [ele[1] for ele in topAuthors]}

	countries = [ele['country'] for ele in authorList if ele]
	topCountries = Counter(countries).most_common(10)
	parsedResult['topCountries'] = {'labels': [ele[0] for ele in topCountries], 'data': [ele[1] for ele in topCountries]}

	affiliations = [ele['affiliation'] for ele in authorList if ele]
	topAffiliations = Counter(affiliations).most_common(10)
	parsedResult['topAffiliations'] = {'labels': [ele[0] for ele in topAffiliations], 'data': [ele[1] for ele in topAffiliations]}

	return {'infoType': 'author', 'infoData': parsedResult}
	'''

	return {'infoType': 'crossTable', 'infoData': parsedResult}

def getCrossTable():
	"""
	data formats:
	authorLines - submission ID | f name | s name | email | country | affiliation | page | person ID | corresponding
	submissionLines - submission ID | track ID | track name | title | authors | submit time | last update time | form fields | keywords | decision | notified | reviews sent | abstract
	reviewLines - review ID | paper ID? | reviewer ID | reviewer name | unknown | text | scores | overall score | unknown | unknown | unknown | unknown | date | time | recommend?
	"""
	# iterate through submission list, storing each submission id as a key whose values contain author, submission and review details
	# a submission and have multiple authors and multiple reviews
	crossTable = {}
	authorLines = s['authorLines']
	submissionLines = s['submissionLines']
	reviewLines = s['reviewLines']
	# store all submission details with submission ID as the key
	for submissionDetail in submissionLines:
		submissionID = submissionDetail[0]
		crossTable[submissionID] = {}
		crossTable[submissionID]['submission'] = submissionDetail
		crossTable[submissionID]['author'] = []
		crossTable[submissionID]['review'] = []

	# store all author details into submission ID
	for authorDetail in authorLines:
		submissionID = authorDetail[0]
		# append to back if an author already exists
		if len(crossTable[submissionID]['author']) != 0:
			crossTable[submissionID]['author'].append(authorDetail)
		else:
			crossTable[submissionID]['author'] = [authorDetail]

	# store all review details into submission ID
	for reviewDetail in reviewLines:
		submissionID = reviewDetail[1]
		# append to back if a review already exists
		if len(crossTable[submissionID]['review']) != 0:
			crossTable[submissionID]['review'].append(reviewDetail)
		else:
			crossTable[submissionID]['review'] = [reviewDetail]

	return crossTable

if __name__ == "__main__":
	parseCSVFile(fileName)
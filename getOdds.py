from bs4 import BeautifulSoup
import re
import numpy as np
import json
import requests
import datetime
import boto3

BUCKET = 'electabilityodds.com'

def getPcts(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text,'lxml')
    ourTab = soup.findAll('table')[1]

    data = {}
    for row in ourTab.findAll('tr'):
        first = True
        name = ''
        vals = []
        for col in row.findAll('td'):
            if first:
                name = col.text
                first = False
            else:
                dig = col.get('data-odig')
                if dig and float(dig) > 0:
                    vals.append(1.0/(float(dig)))
        if len(vals) >= 5:
            ourVal = np.min(vals)
            if ourVal > 0.000:
                data[name]=ourVal
    norm = 0.0
    for k in data:
        norm += data[k]
    return data

def getOdds(min_pct=0.01):
    data = getPcts('https://www.oddschecker.com/politics/us-politics/us-presidential-election-2020')
    data2 = getPcts('https://www.oddschecker.com/politics/us-politics/us-presidential-election-2020/democrat-candidate')

    odds = {}
    for v in data:
        if v in data and v in data2:
            if data[v] > 0.01:
                odds[v] = data[v]/data2[v]
    return odds

if __name__ == '__main__':
    odds = getOdds()
    f = open("odds.txt","a")
    f.write(datetime.datetime.now().strftime("%a, %d-%b-%Y %I:%M:%S, ") + "," + json.dumps(odds) + "\n")
    if len(odds) > 2:
        f = open('index.html','w')
        f.write("<html><body>\n")
        f.write("<h2>Candiate electability based on betting odds</h2>\n")
        f.write("<h3>Generated " + datetime.datetime.now().strftime("%a, %d-%b-%Y %I:%M:%S, ") + "</h3>\n")
        f.write("<table>\n")
        f.write("<tr style=\"font-weight:bold;\"><td>Candidate</td><td>Odds of winning general if primary is won</td></tr>\n")
        for k in sorted(odds, key=odds.get, reverse=True):
            f.write("<tr><td>" + k + "</td><td>" + "{0:.2%}".format(odds[k]) + "</td></tr>\n")
        f.write("</table></body></html>")
        f.close()
        s3_client = boto3.client('s3')
        response = s3_client.upload_file(Filename='index.html', Bucket=BUCKET, Key='index.html', ExtraArgs={'ACL': 'public-read', 'ContentType': 'text/html'})

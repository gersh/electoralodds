from bs4 import BeautifulSoup
import re
import numpy as np
import json
import requests
import datetime
import predictit
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
                if name == 'Beto ORourke':
                    name = "Beto O'Rourke"
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
    low, high, mid = predictit.get_odds()


    odds = {}
    for v in mid:
        if mid[v] > 0.01 and (high[v] - low[v]) <= .3:
            odds[v] = mid[v]
    return odds, low, high

if __name__ == '__main__':
    odds, low, high = getOdds()
    f = open("odds.txt","a")
    f.write(datetime.datetime.now().strftime("%a, %d-%b-%Y %I:%M:%S, ") + "," + json.dumps({'odds':odds,'high':high,'low':low}) + "\n")
    if len(odds) > 2:
        f = open('index.html','w')
        f.write("<html>\n<head>")
        f.write(""" <!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=UA-140995189-1"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'UA-140995189-1');
</script>
<script async defer src="https://buttons.github.io/buttons.js"></script>
""")
        f.write("<title>Electability Analysis -- Electability for Democratic Presidential Candidate </title><body>\n")
        f.write("<h2>Candidate electability based on betting odds</h2>\n")
        f.write("<h3>Generated " + datetime.datetime.now().strftime("%a, %d-%b-%Y %I:%M:%S") + "</h3>\n")
        f.write("<table>\n")
        f.write("<tr style=\"font-weight:bold;\"><td>Candidate</td><td>Odds of winning general if primary is won</td></tr>\n")
        for k in sorted(odds, key=odds.get, reverse=True):
            f.write("<tr><td>" + k + "</td><td>" + "{0:.2%}".format(odds[k]) + " ( " + "{0:.2%}".format(low[k]) + " - " +  "{0:.2%}".format(high[k]) + " )</td></tr>\n")
        f.write("</table>")
        f.write("<br/><i>Refresh and check back for updated odds</i>")
        f.write("<h4>Technical notes</h4>\n<p>The algorithm takes as inputs the betting odds for the Democratic presidential primary and the 2020 election. Then, the electability odds are calculated using the formula <code>p(winning|nomination) = p(winning presidency)/p(winning nomination)</code>. The ranges come from the difference in odds between betting for or against in the betting odds. The first number is based on the last price bet. </p>")
        f.write("""<a href="https://github.com/gersh/electoralodds">Github</a><a class="github-button" href="https://github.com/gersh/electoralodds/issues" data-icon="octicon-issue-opened" aria-label="Issue gersh/electoralodds on GitHub">Issue</a><a class="github-button" href="https://github.com/gersh/electoralodds/subscription" data-icon="octicon-eye" aria-label="Watch gersh/electoralodds on GitHub">Watch</a>
""")
        f.write("</body></html>")
        f.close()
        s3_client = boto3.client('s3')
        response = s3_client.upload_file(Filename='index.html', Bucket=BUCKET, Key='index.html', ExtraArgs={'ACL': 'public-read', 'ContentType': 'text/html'})



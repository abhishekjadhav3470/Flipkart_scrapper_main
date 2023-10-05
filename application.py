from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
from pymongo.mongo_client import MongoClient
#from pymongo.server_api import ServerApi
import csv

application = Flask(__name__)  # initializing a Flask app
app = application

MONGODB_CONNECTION_STRING = "mongodb+srv://abc:abc@cluster0.lj6xm5o.mongodb.net/?retryWrites=true&w=majority"

@app.route('/', methods=['GET'])  # route to display the home page
@cross_origin()
def homePage():
    return render_template("index.html")

@app.route('/review', methods=['POST', 'GET'])  # route to show review comments in a web UI
@cross_origin()
def index():
    if request.method == 'POST':
        try:
            searchString = request.form['content'].replace(" ", "")
            flipkart_url = "https://www.flipkart.com/search?q=" + searchString
            uClient = uReq(flipkart_url)
            flipkartPage = uClient.read()
            uClient.close()
            flipkart_html = bs(flipkartPage, "html.parser")
            bigboxes = flipkart_html.findAll("div", {"class": "_1AtVbE col-12-12"})
            del bigboxes[0:3]
            box = bigboxes[0]
            productLink = "https://www.flipkart.com" + box.div.div.div.a['href']
            prodRes = requests.get(productLink)
            prodRes.encoding = 'utf-8'
            prod_html = bs(prodRes.text, "html.parser")
            commentboxes = prod_html.find_all('div', {'class': "_16PBlm"})

            filename = searchString + ".csv"
            with open(filename, "w", newline='', encoding='utf-8') as fw:
                headers = ["Product", "Customer Name", "Rating", "Heading", "Comment"]
                writer = csv.DictWriter(fw, fieldnames=headers)
                writer.writeheader()

                reviews = []
                for commentbox in commentboxes:
                    try:
                        name = commentbox.div.div.find_all('p', {'class': '_2sc7ZR _2V5EHH'})[0].text
                    except:
                        name = 'No Name'

                    try:
                        rating = commentbox.div.div.div.div.text
                    except:
                        rating = 'No Rating'

                    try:
                        commentHead = commentbox.div.div.div.p.text
                    except:
                        commentHead = 'No Comment Heading'

                    try:
                        comtag = commentbox.div.div.find_all('div', {'class': ''})
                        custComment = comtag[0].div.text
                    except Exception as e:
                        print("Exception while creating dictionary: ", e)

                    mydict = {"Product": searchString, "Customer Name": name, "Rating": rating, "Heading": commentHead, "Comment": custComment}
                    reviews.append(mydict)

                writer.writerows(reviews)

            client = MongoClient(MONGODB_CONNECTION_STRING)
            #client = MongoClient(MONGODB_CONNECTION_STRING, server_api=ServerApi('1'))
            db = client['Scrapping_data']
            review_col = db['data']
            review_col.insert_many(reviews)
            return render_template('results.html', reviews=reviews[0:(len(reviews) - 1)])
        except Exception as e:
            print('The Exception message is: ', e)
            return 'Something went wrong'
    else:
        return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)

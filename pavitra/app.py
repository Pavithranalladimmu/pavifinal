from flask import Flask, render_template, request, redirect, url_for, session
import pymysql
import boto3
import json
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
import os


ENDPOINT="multiweekdb.clnopyq3sfwe.us-east-1.rds.amazonaws.com"
PORT="3306"
USR="admin"
PASSWORD="multiweekdb"
DBNAME="defaultdb"

ACCESS_Key = 'AKIAYU4AEU76UXI6LWNC'
Secret_Key = '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'
Region = 'us-east-1'


app = Flask(__name__)
app.secret_key = "superKey"

def create_subcriptions(topicArn, protocol, endpoint):
    response = sns.subscribe(TopicArn = topicArn, Protocol=protocol, Endpoint=endpoint, ReturnSubscriptionArn=True)
    return response['SubscriptionArn']

@app.route('/', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        fistname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        password = request.form['password']
        conpassword = request.form['conpassword']

        if password != conpassword:
            return render_template("createanaccount.html", alert = "Passwords are not same")
        try:
            conn =  pymysql.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME)
            cur = conn.cursor()
            cur.execute("INSERT INTO userdetailsPavitra(email,password,firstname,lastname) VALUES(%s,%s,%s,%s);", (email, password, fistname, lastname))
            conn.commit()
            conn.close()
            return render_template("loginpage.html")
        except Exception as e:
            print(e)
            return render_template("createanaccount.html", alert = e)
    else:
        return render_template('createanaccount.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('exampleInputEmail1')
        password = request.form.get('exampleInputPassword1') 
        print(email, password)
        try:
            conn = pymysql.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME)
            cur = conn.cursor()
            cur.execute("SELECT email, password FROM userdetailsPavitra;")
            results = cur.fetchall()
            conn.close()
            lists = {}
            for temp in results:
                lists[temp[0]] = temp[1]
            print(results, lists)
            if email not in  lists.keys():
                return render_template("loginpage.html", alert="Please create an account")

            if email in lists.keys() and lists[email] == password:
                session['mainuser'] = email
                return render_template("secretpage.html")
        
            if email in lists.keys() and lists[email] != password:
                return render_template("loginpage.html", alert="Password is wrong")  
        except Exception as e:
            return render_template("loginpage.html", alert=e)
    else:
        return render_template("loginpage.html")

    


def billingtotable():
    try:
        conn =  pymysql.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME)
        cur = conn.cursor()
        temp2 = cur.execute("SELECT * FROM filebillingPavitra")
        result = cur.fetchall()
        return (True, result)
    except Exception as e:
        return (False, e)



sns = boto3.client('sns',aws_access_key_id = ACCESS_Key, aws_secret_access_key=Secret_Key, region_name=Region)


@app.route('/secretpage', methods=['GET', 'POST'])
def secretpage():
    if request.method == 'POST':
        fileInput = request.files['file']
        nameofthefile = fileInput.filename
        print(fileInput, nameofthefile)
        user1 = request.form['user1']
        user2 = request.form['user2']
        user3 = request.form['user3']
        user4 = request.form['user4']
        user5 = request.form['user5']

        users = [user1, user2, user3, user4, user5]
        print(users)
        bucketLocation = boto3.client('s3', aws_access_key_id=ACCESS_Key, aws_secret_access_key=Secret_Key, region_name=Region)

        bucketLocation.upload_fileobj(fileInput, "pavibucketfinal", nameofthefile)
        timeExpiry = 3000
        bucketUrl = bucketLocation.generate_presigned_url('get_object', Params={'Bucket': 'pavibucketfinal', 'Key': nameofthefile}, ExpiresIn=timeExpiry)
        message = "Check the email and click the link to download the file:\n\n{}".format(bucketUrl)
        topic = sns.create_topic(Name='Pavi')
        for enduser in users:
            if enduser:
                topicArn = topic['TopicArn']
                protocol = 'email'
                endpoint = enduser
                response = create_subcriptions(topicArn, protocol, endpoint)
                sns.publish(TopicArn=topicArn, Subject="Check the email and click the link to download the file  ", Message=message)

        user = session['mainuser']
        conn = pymysql.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME)
        cur = conn.cursor()
        cur.execute("INSERT INTO filebillingPavitra(filename, email) VALUES (%s, %s);", (nameofthefile, user))
        conn.commit()
        conn.close()

        overallresult = billingtotable()
        results = {}
        print(overallresult)
        for record in overallresult[1]:
            results[record[0]] = record[1]
        if overallresult[0]:
            return render_template("billingtable.html", result=results)
        else:
            return render_template("secretPage.html", alert="Something Wrong Happened")
     

    else:
        return render_template("secretPage.html")


@app.before_request
def tables():
    try:
        print("Creating Tables")
        conn = pymysql.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME)
        cur = conn.cursor()
        cur.execute("USE defaultdb;")
        cur.execute("CREATE TABLE userdetailsPavitra(firstname varchar(50), lastname varchar(50), email varchar(50) unique, password varchar(50))")
        conn.commit()
        cur.execute("CREATE TABLE filebillingPavitra(filename varchar(50), email varchar(50));")
        conn.commit()
        conn.close()
        print("Tables created successfully")
    except Exception as e:
        print("Failed to create tables")
        print(e)

   
if __name__ == "__main__":
    app.run(debug=True)



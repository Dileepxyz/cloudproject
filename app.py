from flask import Flask, render_template, request, redirect, \
    url_for, session, send_from_directory, flash
import json
import key_config as keys
import boto3
from boto3.dynamodb.conditions import Key
from werkzeug.utils import secure_filename
import os
from flask_session import Session
import uuid

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config["SESSION_PERMANENT"] = False
app.config['download'] = os.path.join(basedir, 'downloaded')
Session(app)

BUCKET_NAME = keys.BUCKET_NAME

dynamodb = boto3.resource('dynamodb',
                          aws_access_key_id=keys.ACCESS_KEY,
                          aws_secret_access_key=keys.SECRET_KEY,
                          region_name=keys.REGION_NAME
                          )


s3 = boto3.client('s3',
                  aws_access_key_id=keys.ACCESS_KEY,
                  aws_secret_access_key=keys.SECRET_KEY,
                  region_name=keys.REGION_NAME
                  )

lam_client = boto3.client('lambda',
                          aws_access_key_id=keys.ACCESS_KEY,
                          aws_secret_access_key=keys.SECRET_KEY,
                          region_name=keys.REGION_NAME
                          )


def send_emails(email_lst, file_url):
    sender = keys.SENDER_EMAIL

    if file_url:
        payload = {"sender": sender,
                   "recipient": email_lst,
                   "url": file_url
                   }

        result = lam_client.invoke(FunctionName='tigger',
                                   InvocationType='RequestResponse',
                                   Payload=json.dumps(payload))

        ran = result['Payload'].read()
        api_response = json.loads(ran)
        print(api_response)
        return api_response


@app.route('/', methods=['GET', 'POST'])
def home_view():
    if session.get("user"):
        return redirect(url_for('dashboard_view'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        partition_key_value = str(uuid.uuid4())

        if name and email and password:
            # Check if the email already exists in the table
            table = dynamodb.Table('User')
            response = table.query(
                KeyConditionExpression='email = :email',
                ExpressionAttributeValues={
                    ':email': email
                }
            )

            if response.get('Items'):
                # Email already exists, display error message
                flash('Email already exists. Please choose a different email.', 'danger')
            else:
                # Email doesn't exist, proceed with user registration
                table.put_item(
                    Item={
                        "user_id": partition_key_value,
                        'name': name,
                        'email': email,
                        'password': password
                    }
                )
                flash('Registration Complete!', 'success')
                return redirect(url_for('sign_in_view'))
        else:
            flash('Please fill out all fields.', 'danger')

    return render_template('sign-up.html')



@app.route('/sign-in', methods=['GET', 'POST'])
def sign_in_view():
    if session.get("user"):
        return redirect(url_for('dashboard_view'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        table = dynamodb.Table('User')

        response = table.query(
            KeyConditionExpression=Key('email').eq(email)
        )

        items = response['Items']
        name = items[0]['name']

        if password == items[0]['password']:
            session["user"] = name
            flash('You are logged in.', 'success')
            return redirect(url_for('dashboard_view'))
    return render_template('sign-in.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard_view():
    if not session.get("user"):
        return redirect(url_for('sign_in_view'))
    if request.method == 'POST':
        if not os.path.exists(app.config['download']):
            os.makedirs(app.config['download'])

        file = request.files['file']
        email_one = request.form.get('email-one')
        email_two = request.form.get('email-two')
        email_three = request.form.get('email-three')
        email_four = request.form.get('email-four')
        email_five = request.form.get('email-five')
        emails = []
        if email_one:
            emails.append(email_one)
        if email_two:
            emails.append(email_two)
        if email_three:
            emails.append(email_three)
        if email_four:
            emails.append(email_four)
        if email_five:
            emails.append(email_five)

        if file:
            filename = secure_filename(file.filename)
            extension = os.path.splitext(filename)[1]
            f_name = str(uuid.uuid4())
            new_filename = f_name + extension
            file.save(os.path.join(app.config['download'], new_filename))
            s3.upload_file(
                Bucket=BUCKET_NAME,
                Filename=os.path.join(app.config['download'], new_filename),
                Key=new_filename
            )
            table = dynamodb.Table('Log')

            table.put_item(
                Item={
                    'file': new_filename,
                    'count': len(emails)
                }
            )
            url = request.host_url + "download/" + new_filename
            print(url)

            response = send_emails(emails, url)

            flash('File uploaded successfully and Email sent.', 'success')
    return render_template("dashboard.html")


@app.route("/sign-out")
def sign_out_view():
    session["user"] = None
    flash('Successfully logged out!', 'success')
    return redirect(url_for('sign_in_view'))


@app.route("/download/<filename>")
def download_zip(filename):
    table = dynamodb.Table('Log')
    response = table.get_item(
        Key={
            'file': filename
        },
        AttributesToGet=[
            'file', 'count'
        ]
    )

    count = int(response['Item']['count'])
    if count > 0:
        updated_count = int(response['Item']['count']) - 1
        response = table.update_item(
            Key={
                'file': filename
            },
            AttributeUpdates={
                'count': {
                    'Value': updated_count,
                    'Action': 'PUT'
                }
            },
            ReturnValues="UPDATED_NEW"
        )

        if updated_count == 0:
            try:
                print(filename)
                s3.delete_object(Bucket=BUCKET_NAME, Key=filename)
            except Exception as e:
                print(e)
    if count == 0:
        os.remove(os.path.join(app.config['download'], filename))
        flash('File is not available to view.', 'danger')
        return redirect(url_for('dashboard_view'))
    else:
        return send_from_directory(app.config['download'], str(filename))


if __name__ == "__main__":
    app.run(debug=True)
    # app.run(host='0.0.0.0', port=5000)

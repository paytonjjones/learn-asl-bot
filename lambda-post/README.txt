To activate virtual environment:
source lambda-post-venv/bin/activate

Install dependencies:
pip install requests
pip install boto3
pip install praw
pip install beautifulsoup4
pip install aws_cdk.core
pip install aws_cdk.aws_ssm

To test (in virtual environment):
python -c 'import lambda_function; print( lambda_function.lambda_handler("foo", "bar"))'

To deploy:
From lambda-post directory:

Run in terminal:
cd lambda-post-venv/lib/python3.8/site-packages
zip -r ../../../../my-deployment-package.zip .

Go back to lambda-post directory:
cd ../../../../

and run:
zip -g my-deployment-package.zip lambda_function.py
zip -g my-deployment-package.zip utils.py
zip -g my-deployment-package.zip creds


If greater than 50 mb:
Upload to S3 bucket (public)
Copy S3 object URL
Go to Lambda and click on "Upload from..."
Paste the S3 object URL

If less than 50 mb:
Upload directly to lambda

Then:
Test the function

(See "Using a virtual environment" section:
https://docs.aws.amazon.com/lambda/latest/dg/python-package.html)

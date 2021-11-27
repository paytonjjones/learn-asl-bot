To activate virtual environment:
source lambda-post-venv/bin/activate

Install dependencies:
pip install -r requirements.txt

To test (in virtual environment):
python -c 'import lambda_function; print( lambda_function.lambda_handler("foo", "bar"))'

To deploy:

1. Enter lambda-post directory
2. Run in terminal:
cd lambda-post-venv/lib/python3.8/site-packages
zip -r ../../../../my-deployment-package.zip .
3. Go back to lambda-post directory:
cd ../../../../
4. Run:
zip -g my-deployment-package.zip lambda_function.py
zip -g my-deployment-package.zip utils.py
zip -g my-deployment-package.zip creds
5a. If greater than 50 mb:
Upload to S3 bucket (public)
Copy S3 object URL
Go to Lambda and click on "Upload from..."
Paste the S3 object URL
5b. If less than 50 mb:
Upload directly to lambda
6. Test the function via lambda

(See "Using a virtual environment" section:
https://docs.aws.amazon.com/lambda/latest/dg/python-package.html)

### Pytest:

```
$ pytest -m unit
$ pytest -m integration
```

##### Serverless:

### Deployment

In order to deploy the example, you need to run the following command:

```
$ export NODE_TLS_REJECT_UNAUTHORIZED=0
$ serverless deploy
```

### Invocation

After successful deployment, you can invoke the deployed function by using the following command:

```bash
serverless invoke --function lambda_post
```

### Local development

You can invoke your function locally by using the following command:

```bash
serverless invoke local --function lambda_post
```

### Bundling dependencies

In case you would like to include third-party dependencies, you will need to use a plugin called `serverless-python-requirements`. You can set it up by running the following command:

```bash
serverless plugin install -n serverless-python-requirements
```




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

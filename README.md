# Learn ASL Bot

This repository contains AWS Lambda functions that power a bot for the Reddit community [r/learnASL](https://www.reddit.com/r/learnASL/).

The goal of this project is to provide the subreddit with a steady stream of resources for learning American Sign Language (ASL). Users can then passively browse the site to gradually learn new ASL vocabulary, grammar, and techniques.

Currently, the bot relies heavily on [Lifeprint](www.lifeprint.com), an ASL learning resource generously created by Dr. Bill Vicars.

## Gather Lambda

The `gather` lambda scrapes the web for relevant ASL resources. It then uploads the cleaned resources in a standardized format to a DyanmoDB database.

## Post Lambda

The `post` lambda queries the DynamoDB database for a relevant learning resource, and then posts that resource to [r/learnASL](https://www.reddit.com/r/learnASL/) via the Reddit account [hands---free](https://www.reddit.com/user/hands---free/). Upon posting, it updates the record for the posted resource.

## Common Layer - Beta

The common layer allows utilities to be shared across the two lambda functions.

---

## Technical Details

### Testing

Testing for this repository is done with `pytest`. Tests should be run from the root directory with the following commands:

```bash
$ pytest -m unit
$ pytest -m integration
```

### Deployment

This repository utilizes the `serverless` framework. Each lambda can be deployed from its own subfolder using the following command:

```bash
$ serverless deploy
```

If the deployment is done behind a VPN, the following command may first be necessary:

```bash
$ export NODE_TLS_REJECT_UNAUTHORIZED=0
```

Local deployment can be executed using:

```bash
$ serverless invoke local --function post
```

### Bundling dependencies

Third-party Python requirements are stored in the `requirements.txt` for each Lambda and handled via `serverless-python-requirements`. You can set it up by running the following command:

```bash
serverless plugin install -n serverless-python-requirements
```

To install dependencies locally use:

```bash
pip install -r requirements.txt
```

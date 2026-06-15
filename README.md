# SPOT Nudging Bot

## What it does

This bot listens for student messages requesting SPOT sessions and posts in course channels to encourage more students to join. It increases visibility of SPOT sessions so students don't have to remember to check the SPOT channel themselves.

## Background

SPOT is Launch School's peer-led study program, where students sign up for sessions tied to specific courses. This bot automatically notifies the relevant course channel when a new session is requested, so students don't have to manually check for activity.

## Architecture

Built on a serverless AWS architecture:

- **API Gateway** — public HTTPS endpoint that receives Slack webhook events
- **Receiver Lambda** — validates the request and queues it for processing, responding to Slack immediately
- **SQS** — durable queue bridging the receiver and processor, with built-in retries
- **Processor Lambda** — applies business logic and posts to Slack when relevant
- **DynamoDB** — stores every incoming event along with its processing status

## Design decisions

**Why serverless?** This project started on a self-managed VPS running Flask, Gunicorn, nginx, and a self-hosted MongoDB instance. Moving to a serverless architecture removed the need to patch and monitor a server, manage SSL certificates, or worry about data loss from a server failure — while comfortably staying within AWS's free tier given the project's traffic volume.

**Why two Lambda functions?** Slack requires a 2xx response within 3 seconds of sending a webhook event, or it considers the delivery failed and retries. Lambda functions can experience "cold starts" — a delay of typically under 1 second, but occasionally longer — when a function hasn't run recently. Splitting the work into two functions means the receiver (lightweight: signature validation, a database write, and queuing a message) can reliably respond within that window, while the processor (Slack API calls, business logic) runs asynchronously via SQS without time pressure.

**Why DynamoDB?** The access pattern here is simple — write an event, look it up by ID, update its status. DynamoDB's serverless, on-demand model fits that pattern without requiring any database administration, and stays within AWS's free tier at this project's scale.

## Repo structure

```
spot-nudging-lambda/
  layers/shared/python/   # shared code + dependencies (config, database, helpers)
  receiver/handler.py     # Lambda 1 - validates and queues incoming Slack events
  processor/handler.py    # Lambda 2 - applies business logic and posts to Slack
```
provider "aws" {
  region = "us-east-1"
}

# ---------- DynamoDB ----------

resource "aws_dynamodb_table" "spot_nudging_slack_events" {
  name = "spot_nudging_slack_events"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "event_id"

  attribute {
    name = "event_id"
    type = "S"
  }
}

# ---------- IAM Role + Policy Attachments ----------

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "spot_nudging_lambda_role" {
  name = "spot_nudging_lambda_role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
  description = "Allows Lambda functions to call DynamoDB and SQS on your behalf. For use in SPOT nudging project for LS."
}

resource "aws_iam_role_policy_attachment" "dynamodb_attach" {
  role = aws_iam_role.spot_nudging_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

resource "aws_iam_role_policy_attachment" "sqs_attach" {
  role = aws_iam_role.spot_nudging_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSQSFullAccess"
}

resource "aws_iam_role_policy_attachment" "cloudwatch_attach" {
  role = aws_iam_role.spot_nudging_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

# ---------- SQS ----------

resource "aws_sqs_queue" "spot_nudging_queue" {
  name = "spot_nudging_queue"
  sqs_managed_sse_enabled = true
  max_message_size = 1048576
}

# ---------- Lambda shared layer ----------

data "archive_file" "shared_layer" {
  type = "zip"
  source_dir = "${path.module}/../layers/shared"
  output_path = "${path.module}/../build/shared_layer.zip"
}

resource "aws_lambda_layer_version" "spotNudgingShared" {
  layer_name = "spotNudgingShared"
  filename = data.archive_file.shared_layer.output_path
  source_code_hash = data.archive_file.shared_layer.output_base64sha256
  compatible_runtimes = ["python3.14", "python3.12", "python3.13"]
  description = "Includes config, database, and helpers modules + requests package"
}

# ---------- Lambda functions ----------

data "archive_file" "receiver_lambda_py" {
  type = "zip"
  source_file = "${path.module}/../receiver/handler.py"
  output_path = "${path.module}/../receiver/handler.zip"
  output_file_mode = "0666"
}

data "archive_file" "processor_lambda_py" {
  type = "zip"
  source_file = "${path.module}/../processor/handler.py"
  output_path = "${path.module}/../processor/handler.zip"
  output_file_mode = "0666"
}

resource "aws_lambda_function" "spotNudgingReceiver" {
  filename = data.archive_file.receiver_lambda_py.output_path
  source_code_hash = data.archive_file.receiver_lambda_py.output_base64sha256
  function_name = "spotNudgingReceiver"
  role = aws_iam_role.spot_nudging_lambda_role.arn
  handler = "handler.lambda_handler"
  runtime = "python3.14"

  layers = [aws_lambda_layer_version.spotNudgingShared.arn]

  environment {
    variables = {
      SLACK_SIGNING_SECRET = var.slack_signing_secret
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.spot_nudging_slack_events.name
      SQS_QUEUE_URL = aws_sqs_queue.spot_nudging_queue.url
    }
  }
}

resource "aws_lambda_function" "spotFunctionProcessor" {
  filename = data.archive_file.processor_lambda_py.output_path
  source_code_hash = data.archive_file.processor_lambda_py.output_base64sha256
  function_name = "spotFunctionProcessor"
  role = aws_iam_role.spot_nudging_lambda_role.arn
  handler = "handler.lambda_handler"
  runtime = "python3.14"
  timeout = 10

  layers = [aws_lambda_layer_version.spotNudgingShared.arn]

  environment {
    variables = {
      SLACK_BOT_TOKEN = var.slack_bot_token
      SLACK_SPOT_CHANNEL_ID = var.slack_spot_channel_id
      SLACK_APP_ID = var.slack_app_id
      SLACK_SIGNING_SECRET = var.slack_signing_secret
      RB_101_CHANNEL_ID = var.rb_101_channel_id
      RB_110_CHANNEL_ID = var.rb_110_channel_id
      RB_120_CHANNEL_ID = var.rb_120_channel_id
      RB_130_CHANNEL_ID = var.rb_130_channel_id
      JS_101_CHANNEL_ID = var.js_101_channel_id
      JS_110_CHANNEL_ID = var.js_110_channel_id
      JS_120_CHANNEL_ID = var.js_120_channel_id
      JS_130_CHANNEL_ID = var.js_130_channel_id
      PY_101_CHANNEL_ID = var.py_101_channel_id
      PY_110_CHANNEL_ID = var.py_110_channel_id
      PY_120_CHANNEL_ID = var.py_120_channel_id
      PY_130_CHANNEL_ID = var.py_130_channel_id
      LS_170_CHANNEL_ID = var.ls_170_channel_id
      RB_175_CHANNEL_ID = var.rb_175_channel_id
      JS_175_CHANNEL_ID = var.js_175_channel_id
      PY_175_CHANNEL_ID = var.py_175_channel_id
      LS_180_CHANNEL_ID = var.ls_180_channel_id
      JS_210_CHANNEL_ID = var.js_210_channel_id
      LS_215_CHANNEL_ID = var.ls_215_channel_id
      JS_225_CHANNEL_ID = var.js_225_channel_id
      JS_230_CHANNEL_ID = var.js_230_channel_id
      TS_240_CHANNEL_ID = var.ts_240_channel_id
      LS_250_CHANNEL_ID = var.ls_250_channel_id
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.spot_nudging_slack_events.name
      SQS_QUEUE_URL = aws_sqs_queue.spot_nudging_queue.url
    }
  }
}

# ---------- Connect SQS to trigger processor lambda ----------

resource "aws_lambda_event_source_mapping" "sqs_to_processor" {
  event_source_arn = aws_sqs_queue.spot_nudging_queue.arn
  function_name = aws_lambda_function.spotFunctionProcessor.arn
  batch_size = 1
}

# ---------- API gateway ----------

resource "aws_apigatewayv2_api" "spotNudgingAPI" {
  name = "spotNudgingAPI"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "gateway_to_receiver" {
  api_id = aws_apigatewayv2_api.spotNudgingAPI.id
  integration_type = "AWS_PROXY"
  integration_method = "POST"
  integration_uri = aws_lambda_function.spotNudgingReceiver.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "slack_events_route" {
  api_id = aws_apigatewayv2_api.spotNudgingAPI.id
  route_key = "POST /slack/events"
  target = "integrations/${aws_apigatewayv2_integration.gateway_to_receiver.id}"
}

resource "aws_lambda_permission" "invoke_receiver" {
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.spotNudgingReceiver.function_name
  principal = "apigateway.amazonaws.com"
  source_arn = "${aws_apigatewayv2_api.spotNudgingAPI.execution_arn}/*/*/slack/events"
}

resource "aws_apigatewayv2_stage" "stage" {
  api_id = aws_apigatewayv2_api.spotNudgingAPI.id
  name = "$default"
  auto_deploy = true
}
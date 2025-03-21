# Slack Webhook Setup Guide

This document provides detailed instructions for setting up and configuring Slack webhooks for the Snowfall Alert System.

## Overview

The Snowfall Alert System uses Slack webhooks to send two types of messages:

1. Snowfall alerts when significant snow is detected at monitored resorts
2. System status updates for monitoring and troubleshooting

## Prerequisites

- Admin access to a Slack workspace
- Permission to create Slack apps

## Step 1: Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click the "Create New App" button
3. Select "From scratch"
4. Enter app details:
   - App Name: "Snowfall Alert System"
   - Workspace: Select your workspace
5. Click "Create App"

![Create Slack App](../assets/slack-create-app.png)

## Step 2: Create Slack Channels

Create two channels in your Slack workspace:

1. **Alerts Channel**:

   - Name: `#snow-alerts`
   - Purpose: Receive notifications about significant snowfall events
   - Privacy: Public or private based on preference

2. **Monitoring Channel**:
   - Name: `#snowalert-monitoring`
   - Purpose: Receive system status updates and diagnostic information
   - Privacy: Private (typically only needed by you)

## Step 3: Enable Incoming Webhooks

1. In your Slack app settings, navigate to "Features" > "Incoming Webhooks"
2. Toggle "Activate Incoming Webhooks" to ON
3. Click "Add New Webhook to Workspace"

![Enable Webhooks](../assets/slack-enable-webhooks.png)

## Step 4: Create Alert Channel Webhook

1. From the "Add new webhook" screen, select the `#snow-alerts` channel
2. Click "Allow"
3. You'll be returned to the Incoming Webhooks page
4. Copy the Webhook URL that appears (it will start with `https://hooks.slack.com/services/`)
5. Save this URL as your `SLACK_WEBHOOK_URL` environment variable

## Step 5: Create Monitoring Channel Webhook

1. Scroll to the bottom of the Incoming Webhooks page
2. Click "Add New Webhook to Workspace" again
3. From the "Add new webhook" screen, select the `#snowalert-monitoring` channel
4. Click "Allow"
5. Copy the new Webhook URL that appears
6. Save this URL as your `SLACK_MONITORING_WEBHOOK_URL` environment variable

## Step 6: Configure App Display

1. Navigate to "Settings" > "Basic Information"
2. Under "Display Information", configure:
   - App Name: "Snowfall Alert System"
   - Short Description: "Real-time alerts for fresh snowfall at ski resorts"
   - App Icon: Upload a snowflake or mountain icon
   - Background Color: #2c3e50 (or your preference)
3. Click "Save Changes"

![App Display Settings](../assets/slack-display-settings.png)

## Step 7: Test the Webhooks

You can test the webhooks using curl or any HTTP client:

```bash
# Test Alert Channel Webhook
curl -X POST -H 'Content-type: application/json' \
--data '{"text":"This is a test alert from the Snowfall Alert System"}' \
YOUR_SLACK_WEBHOOK_URL

# Test Monitoring Channel Webhook
curl -X POST -H 'Content-type: application/json' \
--data '{"text":"This is a test status update from the Snowfall Alert System"}' \
YOUR_SLACK_MONITORING_WEBHOOK_URL
```

You should see the messages appear in their respective channels.

## Message Formatting

### Alert Messages

Alert messages use Slack's Block Kit format for rich formatting:

```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "🏔️ Heavy Snow Alert: Park City Mountain"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*8.5 inches* of fresh snow at *Park City Mountain*!"
      }
    },
    {
      "type": "context",
      "elements": [
        {
          "type": "mrkdwn",
          "text": "Recorded at: 2023-03-21 06:00 MT"
        }
      ]
    }
  ]
}
```

This produces a well-formatted message with a header, snow information, and timestamp.

### Monitoring Messages

Status updates use a similar format but include additional information:

```json
{
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*✅ Operational*\n*Time:* 2023-03-21 06:00:00 MT\n*Resorts Checked:* 10"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Resort Conditions:*\n• Park City Mountain: 2.5\" in last 24h\n• Deer Valley: 1.8\" in last 24h\n..."
      }
    }
  ]
}
```

## Security Considerations

Webhook URLs contain authentication tokens. Treat them as sensitive credentials:

- Store webhook URLs in environment variables, never in code
- Don't share webhook URLs in public repositories
- Rotate webhook URLs if they're ever compromised
- Use separate webhooks for different channels to limit exposure

## Troubleshooting

### Common Issues

1. **Message Not Appearing**

   - Verify the webhook URL is correct
   - Check that the channel still exists
   - Ensure proper JSON formatting in requests

2. **Invalid Payload Error**

   - Check your JSON structure for errors
   - Ensure all required fields are present
   - Verify text fields don't exceed length limits

3. **Rate Limiting**
   - If sending many messages, add delays between requests
   - Standard workspaces are limited to 1 message per second

### Webhook Validation

If you suspect a webhook isn't working:

1. Test with a minimal payload:

   ```json
   { "text": "Testing webhook" }
   ```

2. Check the HTTP response:
   - Success: `200 OK` with body `ok`
   - Error: Will return an error message

## Customizing Notifications

To customize how notifications appear in Slack:

1. **Notification Preferences**:

   - In Slack, right-click the channel name
   - Select "Notification preferences"
   - Configure alerts for All new messages, Mentions, or Nothing

2. **Mobile Notifications**:
   - Configure in Slack mobile app settings
   - Enable notifications for important channels
   - Set up Do Not Disturb schedules if needed

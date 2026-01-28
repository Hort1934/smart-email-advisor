# SSM Session Manager Access Guide

This guide explains how to access your EC2 instance using AWS Systems Manager Session Manager, which provides secure access without SSH keys or security group rules.

## Benefits of SSM Session Manager

✅ **No SSH keys required** - Access via AWS IAM  
✅ **No security group rules** - Works through AWS API  
✅ **Encrypted sessions** - All traffic encrypted  
✅ **Session logging** - All sessions are logged  
✅ **Console access** - Works through AWS Console  
✅ **Port forwarding** - Forward local ports to instance  

## Prerequisites

1. **AWS CLI installed and configured**
   ```bash
   aws --version
   aws configure
   ```

2. **Session Manager Plugin installed** (for port forwarding)
   ```bash
   # macOS
   brew install --cask session-manager-plugin
   
   # Linux
   curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/linux_64bit/session-manager-plugin.rpm" -o "session-manager-plugin.rpm"
   sudo yum install -y session-manager-plugin.rpm
   ```

## Access Methods

### Method 1: AWS CLI Command

```bash
# Get instance ID from Terraform outputs
terraform output instance_id

# Start SSM session
aws ssm start-session --target i-xxxxxxxxxxxxx

# Or use the output command directly
terraform output -raw ssm_session_command
```

### Method 2: AWS Console

1. Go to **AWS Systems Manager** → **Session Manager**
2. Click **Start session**
3. Select your instance
4. Click **Start session**

Or use the direct URL from Terraform outputs:
```bash
terraform output -raw ssm_session_manager_url
```

### Method 3: Port Forwarding

Forward local port to instance:

```bash
# Forward local port 8080 to instance port 80
aws ssm start-session \
  --target i-xxxxxxxxxxxxx \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["80"],"localPortNumber":["8080"]}'

# Then access http://localhost:8080
```

## Common Commands

### Check SSM Agent Status

Once connected via SSM:

```bash
# Check if SSM agent is running
sudo systemctl status amazon-ssm-agent

# Restart SSM agent if needed
sudo systemctl restart amazon-ssm-agent
```

### View Application Logs

```bash
# Docker logs
sudo docker compose -f /opt/smart-email-advisor/docker-compose.prod.yml logs -f

# System logs
sudo journalctl -u amazon-ssm-agent -f
```

### Run Commands via SSM

```bash
# Run a single command
aws ssm send-command \
  --instance-ids "i-xxxxxxxxxxxxx" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["docker ps"]'
```

## Troubleshooting

### SSM Agent Not Running

```bash
# Connect via SSH first (if available)
ssh -i key.pem ubuntu@ELASTIC_IP

# Install SSM agent
sudo snap install amazon-ssm-agent --classic

# Start service
sudo systemctl start snap.amazon-ssm-agent.amazon-ssm-agent.service
sudo systemctl enable snap.amazon-ssm-agent.amazon-ssm-agent.service
```

### IAM Permissions

Ensure your AWS user/role has these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:StartSession"
      ],
      "Resource": [
        "arn:aws:ec2:*:*:instance/*",
        "arn:aws:ssm:*:*:document/AWS-StartSession"
      ],
      "Condition": {
        "StringEquals": {
          "ssm:resourceTag/Project": "Smart Email Advisor"
        }
      }
    }
  ]
}
```

### Instance Not Appearing in SSM

1. **Check IAM role** - Instance must have SSM role attached
2. **Check SSM agent** - Agent must be running
3. **Check network** - Instance needs internet access (for SSM service)
4. **Wait a few minutes** - New instances may take 2-3 minutes to register

### Verify SSM Setup

```bash
# Check instance is registered
aws ssm describe-instance-information \
  --filters "Key=InstanceIds,Values=i-xxxxxxxxxxxxx"

# Check IAM role
aws ec2 describe-instances --instance-ids i-xxxxxxxxxxxxx \
  --query 'Reservations[0].Instances[0].IamInstanceProfile'
```

## Security Best Practices

1. **Use SSM instead of SSH** when possible
2. **Restrict SSH security group** to your IP only
3. **Enable CloudWatch logging** for SSM sessions
4. **Use IAM policies** to control SSM access
5. **Rotate IAM credentials** regularly

## Advanced: Port Forwarding for Application Access

Forward application ports through SSM:

```bash
# Forward backend API (port 8000)
aws ssm start-session \
  --target i-xxxxxxxxxxxxx \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["8000"],"localPortNumber":["8000"]}'

# Forward database (port 5432)
aws ssm start-session \
  --target i-xxxxxxxxxxxxx \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["5432"],"localPortNumber":["5432"]}'
```

## Comparison: SSM vs SSH

| Feature | SSM Session Manager | SSH |
|---------|-------------------|-----|
| Keys Required | ❌ No | ✅ Yes |
| Security Group Rules | ❌ No | ✅ Yes |
| Encryption | ✅ Yes | ✅ Yes |
| Session Logging | ✅ Yes | ⚠️ Optional |
| Port Forwarding | ✅ Yes | ✅ Yes |
| Console Access | ✅ Yes | ❌ No |
| Setup Complexity | ✅ Simple | ⚠️ Medium |

## Resources

- [AWS Session Manager Documentation](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)
- [Session Manager Plugin Installation](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)
- [IAM Permissions for Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/getting-started-restrict-access-quickstart.html)

---

**Tip**: Use SSM Session Manager as your primary access method for better security and easier management!

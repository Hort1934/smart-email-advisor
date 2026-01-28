output "instance_id" {
  description = "EC2 Instance ID"
  value       = aws_instance.app.id
}

output "instance_public_ip" {
  description = "EC2 Instance Public IP (Elastic IP)"
  value       = aws_eip.app_eip.public_ip
}

output "instance_public_dns" {
  description = "EC2 Instance Public DNS"
  value       = aws_instance.app.public_dns
}

output "elastic_ip" {
  description = "Elastic IP Address"
  value       = aws_eip.app_eip.public_ip
}

output "ssh_command" {
  description = "SSH command to connect to instance"
  value       = var.create_key_pair ? "ssh -i ${path.module}/${var.project_name}-key.pem ${var.instance_user}@${aws_eip.app_eip.public_ip}" : "ssh -i ${var.ssh_key_path} ${var.instance_user}@${aws_eip.app_eip.public_ip}"
}

output "application_url" {
  description = "Application URL"
  value       = "http://${aws_eip.app_eip.public_ip}"
}

output "deployment_command" {
  description = "Command to deploy application"
  value       = "cd .. && ./deploy.sh ${var.instance_user}@${aws_eip.app_eip.public_ip}"
}

output "key_pair_name" {
  description = "Name of the key pair (created or existing)"
  value       = var.create_key_pair ? (try(aws_key_pair.app_key_pair.key_name, "")) : var.key_pair_name
}

output "private_key_path" {
  description = "Path to the private key file (if created)"
  value       = var.create_key_pair ? "${path.module}/${var.project_name}-key.pem" : "N/A (using existing key)"
}

output "ssm_session_command" {
  description = "AWS CLI command to start SSM session"
  value       = "aws ssm start-session --target ${aws_instance.app.id}"
}

output "ssm_session_manager_url" {
  description = "AWS Console URL for SSM Session Manager"
  value       = "https://${var.aws_region}.console.aws.amazon.com/systems-manager/session-manager/${aws_instance.app.id}"
}

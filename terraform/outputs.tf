output "instance_public_ip" {
  description = "Public IP of the Container-Pulse EC2 instance"
  value       = aws_instance.container_pulse.public_ip
}

output "instance_id" {
  description = "EC2 Instance ID"
  value       = aws_instance.container_pulse.id
}

output "dashboard_url" {
  description = "Container-Pulse dashboard URL"
  value       = "http://${aws_instance.container_pulse.public_ip}:8888"
}

output "prometheus_url" {
  description = "Prometheus URL"
  value       = "http://${aws_instance.container_pulse.public_ip}:9090"
}

output "grafana_url" {
  description = "Grafana URL"
  value       = "http://${aws_instance.container_pulse.public_ip}:3000"
}

output "ssh_command" {
  description = "SSH into the instance"
  value       = "ssh -i ~/.ssh/id_rsa ubuntu@${aws_instance.container_pulse.public_ip}"
}

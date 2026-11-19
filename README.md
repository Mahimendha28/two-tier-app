# ScaleStack: Auto-Scaling 2-Tier Web App on AWS

A highly available 2-tier web application deployed on AWS. A Flask to-do app runs on EC2 instances behind an **Application Load Balancer**, an **Auto Scaling Group** adds servers automatically when CPU load rises, and all servers share one **Amazon RDS MySQL** database.

## Objective

- Distribute traffic across multiple servers with an Application Load Balancer
- Scale compute capacity automatically based on CPU utilization
- Keep data consistent across all servers with a shared managed database
- Deploy the app automatically on every new instance, with no manual setup

## Architecture

```
User (Browser)
      |
      v
Application Load Balancer (public DNS, port 80)
      |
      v
Target Group (health check: /health)
      |
      v
Auto Scaling Group (Min 1, Desired 1, Max 2)
EC2 Ubuntu instances: Nginx -> Gunicorn -> Flask
      |
      v
Amazon RDS MySQL 8.4 (private, not publicly accessible)
```

| Tier | Component |
|---|---|
| Application tier | Nginx (reverse proxy, port 80) + Gunicorn + Flask on EC2 |
| Database tier | Amazon RDS MySQL |

## Tech Stack

- **AWS:** EC2, Launch Templates, Auto Scaling, Application Load Balancer, Target Groups, RDS MySQL, CloudWatch, VPC, Security Groups
- **Software:** Ubuntu, Nginx, Gunicorn, Flask, Python, PyMySQL
- **Tools:** Git, GitHub

## Repository Structure

```
two-tier-app/
├── app.py              # Flask application (add / view / delete tasks, /health endpoint)
├── requirements.txt    # flask, pymysql, gunicorn
├── user-data.sh        # Launch template user data (placeholders for secrets)
├── README.md
└── screenshots/        # Architecture and demo screenshots
```

## How It Works

1. Users open the **ALB DNS name** in the browser.
2. The ALB forwards each request to a healthy EC2 instance in the target group.
3. Nginx passes the request to Gunicorn, which runs the Flask app.
4. Flask reads and writes tasks in the shared **RDS MySQL** database.
5. Each page shows the hostname of the server that handled the request ("Served by"), which makes load balancing visible.
6. CloudWatch monitors CPU. When it is high, the Auto Scaling Group launches a new instance. The instance runs the **user data** script, which installs the software, clones this repo and starts the app. After it passes the health check, the ALB sends traffic to it.

## Security Groups (least privilege)

| Security group | Inbound rule |
|---|---|
| ALB SG | HTTP 80 from anywhere |
| EC2 SG | HTTP 80 from the ALB SG (SSH 22 from my IP for debugging) |
| RDS SG | MySQL 3306 from the EC2 SG only |

The database is not publicly accessible.

## Setup Guide

### 1. Database
1. Create an RDS MySQL instance in the same VPC as the EC2 instances.
2. Set **Public access = No** and attach the RDS security group.
3. Set the initial database name to `appdb`.
4. Copy the RDS endpoint.

### 2. Launch template
1. Create a launch template: Ubuntu AMI, `t3.micro`, key pair, EC2 security group.
2. Paste `user-data.sh` into **Advanced details > User data**.
3. Replace `YOUR_RDS_ENDPOINT` and `YOUR_PASSWORD` with your real values (never commit them to GitHub).

### 3. Load balancer
1. Create a target group (HTTP 80, health check path `/health`).
2. Create an internet-facing ALB in at least 2 Availability Zones and attach the target group.

### 4. Auto Scaling Group
1. Create an ASG from the launch template, in 2 subnets in different AZs.
2. Attach it to the target group.
3. Set **Min 1, Desired 1, Max 2**.
4. Add a scaling policy, for example:
   - **Scale out:** CloudWatch alarm CPU > 40% for 1 minute, add 1 instance
   - **Scale in:** CloudWatch alarm CPU < 10% for 2 minutes, remove 1 instance

### 5. Test
Open `http://<ALB-DNS-name>`, add a few tasks and refresh.

## Auto Scaling Test

1. Connect to the running instance and generate CPU load:
   ```bash
   sudo apt-get install -y stress
   stress --cpu 1 --timeout 900
   ```
2. Watch **ASG > Activity**. CloudWatch detects the high CPU and the ASG launches a second instance.
3. When the new instance is healthy, refresh the ALB URL. The **Served by** hostname changes between servers while the tasks stay the same.
4. Stop the load:
   ```bash
   sudo pkill stress
   ```
5. CPU falls, and the ASG scales back in to 1 instance.

## Results

- Automatic scale-out from 1 to 2 instances under CPU load
- Traffic shared across instances by the ALB
- Data stayed consistent across instances because both use the same RDS database
- New instances deploy the app by themselves through user data

## Challenges and Solutions

| Problem | Solution |
|---|---|
| Nginx install failed in user data | Added `-y` to `apt-get install`, since user data is non-interactive |
| User data changes had no effect | User data runs only on first boot, so I created a new template version and ran an instance refresh |
| Old page still showing | The ALB was still serving old instances, so they had to be replaced |
| App could not reach the database | Allowed port 3306 from the EC2 security group and confirmed the same VPC |
| Slow scale-in with target tracking | Used CloudWatch alarm-based scaling policies for faster scale-in |
| Data differing between servers | Used one shared RDS database instead of a database on each instance |

## Key Learnings

- How launch templates, user data and Auto Scaling work together
- Why application servers should be stateless and data should live in a shared database
- How security groups isolate each layer
- How health checks and target groups affect traffic routing
- Troubleshooting with `cloud-init-output.log`, `systemctl` and `journalctl`

## Cost Control

ALB and RDS charge hourly even when idle. After testing:

1. Set the ASG to Min 0, Desired 0
2. Take a manual RDS snapshot, then delete the database
3. Delete the ALB (the target group, launch template and security groups are free to keep)
4. Set a budget alert in AWS Billing



## Future Improvements

- HTTPS with ACM and a custom domain
- Store database credentials in AWS Secrets Manager instead of user data
- Put the instances in private subnets behind a NAT gateway
- Multi-AZ RDS for database high availability
- Infrastructure as code with Terraform or CloudFormation

## Author

**Mahi Mendha**
GitHub: [Mahimendha28](https://github.com/Mahimendha28)
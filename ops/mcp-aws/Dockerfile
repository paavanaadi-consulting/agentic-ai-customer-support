FROM python:3.10-slim

WORKDIR /app

# Install required system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    netcat-openbsd \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Clone the MCP repository
RUN git clone https://github.com/awslabs/mcp.git /tmp/mcp-repo

# Install the core MCP server components
RUN cd /tmp/mcp-repo/src/core-mcp-server && pip install -e .

# Install all AWS-related MCP server components
RUN cd /tmp/mcp-repo/src/lambda-tool-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/amazon-sns-sqs-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/amazon-mq-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/amazon-kendra-index-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/amazon-keyspaces-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/amazon-neptune-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/amazon-qindex-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/amazon-rekognition-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/aws-bedrock-data-automation-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/aws-diagram-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/aws-documentation-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/aws-healthomics-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/aws-location-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/aws-serverless-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/aws-support-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/bedrock-kb-retrieval-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/cdk-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/cfn-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/cloudwatch-logs-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/cost-analysis-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/cost-explorer-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/dynamodb-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/ecs-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/eks-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/iam-mcp-server && pip install -e .
RUN cd /tmp/mcp-repo/src/stepfunctions-tool-mcp-server && pip install -e .

# Copy scripts and configuration files
COPY entrypoint.sh .
COPY config/ ./config/
COPY health_check.sh .

# Make scripts executable
RUN chmod +x entrypoint.sh health_check.sh

# Expose ports for each MCP server
# Lambda Tool MCP Server
EXPOSE 8766
# Messaging (SNS/SQS) MCP Server
EXPOSE 8767
# MQ MCP Server
EXPOSE 8768
# Kendra MCP Server
EXPOSE 8769
# Keyspaces MCP Server
EXPOSE 8770
# Neptune MCP Server
EXPOSE 8771
# QIndex MCP Server
EXPOSE 8772
# Rekognition MCP Server
EXPOSE 8773
# Bedrock Data Automation MCP Server
EXPOSE 8774
# AWS Diagram MCP Server
EXPOSE 8775
# AWS Documentation MCP Server
EXPOSE 8776
# AWS HealthOmics MCP Server
EXPOSE 8777
# AWS Location MCP Server
EXPOSE 8778
# AWS Serverless MCP Server
EXPOSE 8779
# AWS Support MCP Server
EXPOSE 8780
# Bedrock KB Retrieval MCP Server
EXPOSE 8781
# CDK MCP Server
EXPOSE 8782
# CloudFormation MCP Server
EXPOSE 8783
# CloudWatch Logs MCP Server
EXPOSE 8784
# Cost Analysis MCP Server
EXPOSE 8785
# Cost Explorer MCP Server
EXPOSE 8786
# DynamoDB MCP Server
EXPOSE 8787
# ECS MCP Server
EXPOSE 8788
# EKS MCP Server
EXPOSE 8789
# IAM MCP Server
EXPOSE 8790
# Step Functions MCP Server
EXPOSE 8791

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV AWS_MCP_LAMBDA_PORT=8766
ENV AWS_MCP_MESSAGING_PORT=8767
ENV AWS_MCP_MQ_PORT=8768
ENV AWS_MCP_KENDRA_PORT=8769
ENV AWS_MCP_KEYSPACES_PORT=8770
ENV AWS_MCP_NEPTUNE_PORT=8771
ENV AWS_MCP_QINDEX_PORT=8772
ENV AWS_MCP_REKOGNITION_PORT=8773
ENV AWS_MCP_BEDROCK_DATA_PORT=8774
ENV AWS_MCP_DIAGRAM_PORT=8775
ENV AWS_MCP_DOCUMENTATION_PORT=8776
ENV AWS_MCP_HEALTHOMICS_PORT=8777
ENV AWS_MCP_LOCATION_PORT=8778
ENV AWS_MCP_SERVERLESS_PORT=8779
ENV AWS_MCP_SUPPORT_PORT=8780
ENV AWS_MCP_BEDROCK_KB_PORT=8781
ENV AWS_MCP_CDK_PORT=8782
ENV AWS_MCP_CFN_PORT=8783
ENV AWS_MCP_CLOUDWATCH_LOGS_PORT=8784
ENV AWS_MCP_COST_ANALYSIS_PORT=8785
ENV AWS_MCP_COST_EXPLORER_PORT=8786
ENV AWS_MCP_DYNAMODB_PORT=8787
ENV AWS_MCP_ECS_PORT=8788
ENV AWS_MCP_EKS_PORT=8789
ENV AWS_MCP_IAM_PORT=8790
ENV AWS_MCP_STEPFUNCTIONS_PORT=8791

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command - can be overridden
CMD ["all"]

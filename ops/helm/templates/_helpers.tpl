{{/*
Expand the name of the chart.
*/}}
{{- define "agentic-ai-customer-support.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "agentic-ai-customer-support.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "agentic-ai-customer-support.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "agentic-ai-customer-support.labels" -}}
helm.sh/chart: {{ include "agentic-ai-customer-support.chart" . }}
{{ include "agentic-ai-customer-support.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "agentic-ai-customer-support.selectorLabels" -}}
app.kubernetes.io/name: {{ include "agentic-ai-customer-support.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "agentic-ai-customer-support.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "agentic-ai-customer-support.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
API service name
*/}}
{{- define "agentic-ai-customer-support.api.fullname" -}}
{{- printf "%s-api" (include "agentic-ai-customer-support.fullname" .) }}
{{- end }}

{{/*
MCP Postgres service name
*/}}
{{- define "agentic-ai-customer-support.mcp-postgres.fullname" -}}
{{- printf "%s-mcp-postgres" (include "agentic-ai-customer-support.fullname" .) }}
{{- end }}

{{/*
MCP Kafka service name
*/}}
{{- define "agentic-ai-customer-support.mcp-kafka.fullname" -}}
{{- printf "%s-mcp-kafka" (include "agentic-ai-customer-support.fullname" .) }}
{{- end }}

{{/*
Consumer service name
*/}}
{{- define "agentic-ai-customer-support.consumer.fullname" -}}
{{- printf "%s-consumer" (include "agentic-ai-customer-support.fullname" .) }}
{{- end }}

{{/*
Qdrant service name
*/}}
{{- define "agentic-ai-customer-support.qdrant.fullname" -}}
{{- printf "%s-qdrant" (include "agentic-ai-customer-support.fullname" .) }}
{{- end }}

{{/*
Generate database connection string
*/}}
{{- define "agentic-ai-customer-support.databaseUrl" -}}
{{- if .Values.postgresql.enabled }}
postgresql://{{ .Values.postgresql.auth.username }}:{{ .Values.postgresql.auth.password }}@{{ include "agentic-ai-customer-support.fullname" . }}-postgresql:5432/{{ .Values.postgresql.auth.database }}
{{- else }}
{{- .Values.externalDatabase.url }}
{{- end }}
{{- end }}

{{/*
Generate Kafka bootstrap servers
*/}}
{{- define "agentic-ai-customer-support.kafkaBootstrapServers" -}}
{{- if .Values.kafka.enabled }}
{{ include "agentic-ai-customer-support.fullname" . }}-kafka:9092
{{- else }}
{{- .Values.externalKafka.bootstrapServers }}
{{- end }}
{{- end }}

{{/*
Generate Qdrant URL
*/}}
{{- define "agentic-ai-customer-support.qdrantUrl" -}}
{{- if .Values.qdrant.enabled }}
http://{{ include "agentic-ai-customer-support.fullname" . }}-qdrant:6333
{{- else }}
{{- .Values.externalQdrant.url }}
{{- end }}
{{- end }}

{{/*
Common environment variables
*/}}
{{- define "agentic-ai-customer-support.commonEnv" -}}
- name: DATABASE_URL
  value: {{ include "agentic-ai-customer-support.databaseUrl" . | quote }}
- name: KAFKA_BOOTSTRAP_SERVERS
  value: {{ include "agentic-ai-customer-support.kafkaBootstrapServers" . | quote }}
- name: QDRANT_URL
  value: {{ include "agentic-ai-customer-support.qdrantUrl" . | quote }}
- name: LOG_LEVEL
  value: {{ .Values.api.env.LOG_LEVEL | quote }}
- name: RELEASE_NAME
  value: {{ .Release.Name | quote }}
- name: RELEASE_NAMESPACE
  value: {{ .Release.Namespace | quote }}
{{- end }}

{{/*
Generate storage class
*/}}
{{- define "agentic-ai-customer-support.storageClass" -}}
{{- if .Values.global.storageClass }}
{{- .Values.global.storageClass }}
{{- else if .Values.cloudProvider.aws.enabled }}
{{- .Values.cloudProvider.aws.storageClass }}
{{- else if .Values.cloudProvider.azure.enabled }}
{{- .Values.cloudProvider.azure.storageClass }}
{{- else if .Values.cloudProvider.gcp.enabled }}
{{- .Values.cloudProvider.gcp.storageClass }}
{{- else }}
standard
{{- end }}
{{- end }}

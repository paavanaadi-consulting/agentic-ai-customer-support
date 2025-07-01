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
Common environment variables
*/}}
{{- define "agentic-ai-customer-support.commonEnv" -}}
- name: NAMESPACE
  valueFrom:
    fieldRef:
      fieldPath: metadata.namespace
- name: POD_NAME
  valueFrom:
    fieldRef:
      fieldPath: metadata.name
- name: POD_IP
  valueFrom:
    fieldRef:
      fieldPath: status.podIP
{{- end }}

{{/*
Database connection environment variables
*/}}
{{- define "agentic-ai-customer-support.dbEnv" -}}
- name: POSTGRES_HOST
  value: {{ include "agentic-ai-customer-support.fullname" . }}-postgresql
- name: POSTGRES_PORT
  value: "5432"
- name: POSTGRES_DB
  value: {{ .Values.postgresql.auth.database }}
- name: POSTGRES_USER
  value: {{ .Values.postgresql.auth.username }}
- name: POSTGRES_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "agentic-ai-customer-support.fullname" . }}-postgresql
      key: password
{{- end }}

{{/*
Kafka connection environment variables
*/}}
{{- define "agentic-ai-customer-support.kafkaEnv" -}}
- name: KAFKA_BOOTSTRAP_SERVERS
  value: {{ include "agentic-ai-customer-support.fullname" . }}-kafka:9092
{{- end }}

{{/*
Qdrant connection environment variables
*/}}
{{- define "agentic-ai-customer-support.qdrantEnv" -}}
- name: QDRANT_HOST
  value: {{ include "agentic-ai-customer-support.qdrant.fullname" . }}
- name: QDRANT_PORT
  value: "6333"
{{- end }}

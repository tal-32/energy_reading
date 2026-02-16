{{/* Common labels - Applied to all resources */}}
{{- define "energy-reading.labels" -}}
assignment-id: {{ .Values.global.assignmentId | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end }}

{{/* Selector labels - Used to link Services to Pods (Keep these stable!) */}}
{{- define "producer.selectorLabels" -}}
app: producer
{{- end }}

{{- define "consumer.selectorLabels" -}}
app: consumer
{{- end }}

{{- define "frontend.selectorLabels" -}}
app: frontend
{{- end }}

{{- define "redis.selectorLabels" -}}
app: redis
{{- end }}

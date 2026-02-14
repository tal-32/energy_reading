{{/* Common labels */}}
{{- define "energy-reading.labels" -}}
assignment-id: {{ .Values.global.assignmentId | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/* Selector labels for Producer */}}
{{- define "producer.selectorLabels" -}}
app: producer
assignment-id: {{ .Values.global.assignmentId | quote }}
{{- end }}

{{/* Selector labels for Consumer */}}
{{- define "consumer.selectorLabels" -}}
app: consumer
assignment-id: {{ .Values.global.assignmentId | quote }}
{{- end }}

{{/* Selector labels for Redis */}}
{{- define "redis.selectorLabels" -}}
app: redis
assignment-id: {{ .Values.global.assignmentId | quote }}
{{- end }}
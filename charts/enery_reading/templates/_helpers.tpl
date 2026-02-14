{{/* Common labels */}}
{{- define "energy-reading.labels" -}}
assignment-id: {{ .Values.global.assignmentId | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/* Selector labels */}}
{{- define "producer.selectorLabels" -}}
app: producer
assignment-id: {{ .Values.global.assignmentId | quote }}
{{- end }}

{{- define "consumer.selectorLabels" -}}
app: consumer
assignment-id: {{ .Values.global.assignmentId | quote }}
{{- end }}

{{- define "redis.selectorLabels" -}}
app: redis
assignment-id: {{ .Values.global.assignmentId | quote }}
{{- end }}
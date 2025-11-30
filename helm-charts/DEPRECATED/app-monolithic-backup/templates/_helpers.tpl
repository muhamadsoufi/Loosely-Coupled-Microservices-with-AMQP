{{- define "microservices.fullname" -}}
{{ .Chart.Name }}-{{ .Release.Name }}
{{- end }}

{{- define "microservices.labels" -}}
helm.sh/chart: {{ include "microservices.chart" . }}
{{ include "microservices.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "microservices.chart" -}}
{{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{- end }}

{{- define "microservices.selectorLabels" -}}
app.kubernetes.io/name: {{ include "microservices.chart" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "microservices.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{ default (include "microservices.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{ default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

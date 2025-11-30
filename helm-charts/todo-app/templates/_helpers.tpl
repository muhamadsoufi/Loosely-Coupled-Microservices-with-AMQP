{{- define "todo-app.fullname" -}}
{{ .Chart.Name }}-{{ .Release.Name }}
{{- end }}

{{- define "todo-app.labels" -}}
helm.sh/chart: {{ include "todo-app.chart" . }}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "todo-app.chart" -}}
{{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{- end }}

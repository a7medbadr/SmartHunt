{{- define "smarthunt.name" -}}
smarthunt
{{- end }}

{{- define "smarthunt.fullname" -}}
{{ .Release.Name }}
{{- end }}

{{- define "smarthunt.labels" -}}
app: {{ include "smarthunt.name" . }}
component: backend
{{- end }}

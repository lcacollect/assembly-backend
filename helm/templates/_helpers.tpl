{{- define "serverName" }}
{{- if eq .Values.deployType "PROD"}} "LCA Assembly"{{- else}} "LCA Dev"{{- end}}
{{- end}}
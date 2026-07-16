build:
	oc start-build smarthunt-backend --from-dir=. --wait

deploy:
	oc rollout restart deployment/smarthunt-backend

status:
	oc rollout status deployment/smarthunt-backend

logs:
	oc logs deployment/smarthunt-backend -f

pods:
	oc get pods

route:
	oc get route

health:
	curl -k https://$(shell oc get route smarthunt-backend -o jsonpath='{.spec.host}')/api/v1/health/live

metrics:
	curl -k https://$(shell oc get route smarthunt-backend -o jsonpath='{.spec.host}')/api/v1/metrics

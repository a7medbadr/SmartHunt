build:
	oc start-build smarthunt-backend --from-dir=. --follow --wait

deploy:
	oc rollout restart deployment/smarthunt-backend
	oc rollout status deployment/smarthunt-backend

logs:
	oc logs -f deployment/smarthunt-backend

status:
	oc get pods
	oc get builds
	oc get deployment
	oc get route

test:
	ROUTE=$$(oc get route smarthunt-backend -o jsonpath='{.spec.host}'); \
	echo "=== Jobs Recommendation ==="; \
	curl -sk -X POST \
	-H "Content-Type: application/json" \
	-d '{"resume":"Linux Docker Python OpenShift AWS"}' \
	https://$$ROUTE/api/v1/jobs/recommend; \
	echo; \
	echo "=========================="; \
	echo "=== Career Advice ==="; \
	curl -sk -X POST \
	-H "Content-Type: application/json" \
	-d '{"resume":"Linux Docker Python"}' \
	https://$$ROUTE/api/v1/career/advice; \
	echo; \
	echo "=========================="; \
	curl -sk https://$$ROUTE/api/v1/openapi.json | python3 -m json.tool >/dev/null && echo "OPENAPI_OK"

all: build deploy test

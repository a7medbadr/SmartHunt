// The backend's global exception handler (shared/exceptions.py) reshapes
// every HTTPException into {"error": true, "message": <detail>, "path",
// "request_id"} — NOT FastAPI's default {"detail": ...} shape. Found
// live 2026-08-06 while wiring up specific scan-failure reasons: a test
// asserting `response.json()["detail"]` failed with KeyError even though
// the backend really was returning the right message, just under a
// different key. Any frontend code reading a backend error message must
// use `.message`, not `.detail` (the settings page's change-password
// error handling had this same wrong key, silently never showing the
// real server error — fixed alongside this).
export function getApiErrorMessage(error: unknown): string | undefined {
  return (error as { response?: { data?: { message?: string } } })?.response?.data?.message;
}

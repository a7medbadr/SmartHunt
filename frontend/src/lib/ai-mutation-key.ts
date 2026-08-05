// Shared TanStack Query mutationKey for every mutation that ultimately
// calls the local Ollama model. The backend only runs one generation at
// a time process-wide (ai/providers/ollama.py's _ollama_semaphore) — if
// the user fires off several AI features in a row (deep analysis, then
// cover letter, then interview prep...) without waiting, each one queues
// behind the last, and every queued request's own timeout counts from
// when IT started, not from when it actually got a turn. Confirmed live
// 2026-08-04: four requests fired within minutes of each other took 123s,
// 134s, 258s, and 348-724s respectively to finally resolve — all
// eventually succeeded (100% backend success rate), but the growing
// queue read as "the AI is broken" even though nothing ever failed.
// useIsMutating({ mutationKey: AI_MUTATION_KEY }) lets every AI-triggering
// button across the app disable itself while ANY of them is in flight,
// so a new request can't be queued behind one still running.
export const AI_MUTATION_KEY = ["ai-generation"];

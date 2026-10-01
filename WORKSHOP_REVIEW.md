# Workshop review

The workshop is designed for about 150 minutes of active coding and discussion. These improvements came from reviewing the attendee path from account creation through the final memory search.

| Finding | Improvement made | Learning effect |
| --- | --- | --- |
| Setup and service provisioning could consume the coding time | Added a 150-minute schedule and [instructor preflight](INSTRUCTOR.md) | Attendees reach the coding labs with access ready |
| Lab time could be spent entirely on setup or typing | Added small pace targets that reserve time to predict and explain | Each lab ends with understanding the result |
| Earlier plan guidance incorrectly ruled out Free for Agent Memory | Updated lab 4 to follow the current Redis Cloud service guide's Free Quick create path and kept an instructor fallback | Attendees can try the Free path without being steered toward an unnecessary paid plan |
| Shared Agent Memory constants would mix attendees' fictional sessions | Added `WORKSHOP_USER_ID` and a stable per-attendee session ID | Attendees can see why identity and query scope matter |
| Labs emphasized successful output more than interpretation | Added a prediction and explanation questions to each lab | Attendees connect the result to the stored data and service behavior |
| Cache miss handling should match the chosen RedisVL interface | Lab 3 now uses `LangCacheSemanticCache.check()`, whose empty hit list is a miss | Attendees can identify a cache miss without interpreting the underlying service response object |
| An external embedding key blocked lab 1 for some attendees | Moved to RedisVL's local Hugging Face vectorizer and documented its first download | Attendees can inspect indexing and retrieval without an embedding API key |
| Dense code made the completed examples harder to follow | Split nested result parsing and SDK calls into named steps | The answer key shows the sequence of work clearly |
| The final comparison lacked a facilitator reference | Added a debrief answer key with source, update path, and staleness for each question | Attendees explain when to use each component, beyond a successful printout |
| A successful printout did not always reveal what was stored | Added vector byte length, raw order HASH, and Memory health checks, with a data trace table in the attendee guide | Attendees distinguish stored data, service behavior, and connection failure |

The remaining Cloud check requires service credentials. Lab 1 uses a locally downloaded Hugging Face model through RedisVL, so attendees no longer need an OpenAI key. Lab 3 uses RedisVL's managed LangCache adapter. Offline checks validate imports, sample loading, the vector schema, syntax, links, and the slide deck package; they cannot prove a Cloud service is reachable from an attendee's account.

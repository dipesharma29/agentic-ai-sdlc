# Sample site

A small static site, used as the practice target for the Fix Agent.

- `.agent.json` tells the agent how to run the tests and which paths it must not change.
- Tests: `python -m unittest discover -s tests -q`

A bug is deliberately planted here before a demonstration, so a failing suite in this
folder is often the intended state. See `../../docs/TESTING_THE_AGENT.md`.

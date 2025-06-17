# Conversation AI Real-Time Knowledge (RTK)

Give Eleven Labs Conversational AI agents, knowledge about current events.

## Setup

### Installing Dependencies

```shell
pip install -r requirements.txt
```

### Environment Variables

```text
# Required
ELEVENLABS_API_KEY=
ELEVENLABS_AGENT_ID=


# Plugins
OPENWEATHER_API_KEY=
```

Make sure to omit the `.example` suffix in `.env.example`.

## How to run

Entry point: main.py (load plugins, run plugins, load data to knowledge base, attach agent to document)

`/logs`: Stores all logs, useful for debugging. (Contents git ignored.)
`/output`: Stores all output files that are sent to knowledge base. (Contents git ignored.)
`/plugins`: Stores the different plugins which are called and then attached to knowledge document.

## Plugins

Each plugin requires a `run()` function which is what the main execution loop call on every plugin. Ensure this function exists in each plugin and returns data (in any text format.)
# Toolchain Artifact Contract — V1

Location:
RUN_DIR/toolchain.json

Schema version: "1"

Required fields:

{
"schema_version": "1",
"kprovengine": {
"version": "<package version>",
"entrypoint": "cli"
},
"python": {
"implementation": "CPython",
"version": "3.x.y"
},
"platform": {
"system": "<OS>",
"release": "<OS release>",
"machine": "<arch>"
},
"runtime": {
"in_container": true|false
},
"git": {
"repo": "<url or null>",
"ref": "<branch or null>",
"sha": "<commit or null>"
}
}

Determinism requirements:

- No timestamps.
- Stable key ordering.
- UTF-8.
- Trailing newline.

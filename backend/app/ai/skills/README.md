# AI Skill Contracts

Skill wrappers isolate prompts and providers from backend services.

## Common Rules

- Input is structured Python data.
- Output is structured Python data.
- Skills do not write database rows.
- Skills do not decide job status.
- Skills do not export YAML.
- Services validate and persist every skill output.

## Required V0+V1 Skills

### NovelReaderSkill

Input:

- normalized chapters
- paragraph IDs

Output:

- characters
- events
- foreshadowing candidates
- source refs

### StoryOntologySkill

Input:

- novel analysis
- source refs

Output:

- story bible
- relationship edges
- knowledge states
- voice profiles

### AdaptationPlannerSkill

Input:

- story bible
- events
- causal graph
- adaptation config

Output:

- retained events
- merged events
- deleted or deferred events
- protected elements
- scene plan

### ScreenplayYamlWriterSkill

Input:

- scene plan
- story bible
- adaptation config
- schema summary

Output:

- screenplay JSON structure

Despite the historical name, this skill returns structured data. YAML export is
owned by `backend/app/exporters/yaml_exporter.py`.

## Placeholder Skills

### ContinuityAuditorSkill

Returns minimal audit warnings with concrete target IDs.

### DialogueDoctorSkill

Reserved for V4-style dialogue and subtext refinement.


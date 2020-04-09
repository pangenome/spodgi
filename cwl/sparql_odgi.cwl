#!/usr/bin/env cwl-runner
class: CommandLineTool
cwlVersion: v1.1
hints:
  DockerRequirement:
    dockerPull: spodgi/spodgi
baseCommand: sparql_odgi
arguments:
  - $(inputs.odgi)
  - $(inputs.sparql)
inputs:
  - id: odgi
    type: File
  - id: sparql
    type: string
outputs:
  - id: sparql_result
    type: stdout
stdout: sparql_result.txt

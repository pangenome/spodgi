#!/usr/bin/env cwl-runner
class: CommandLineTool
cwlVersion: v1.1
hints:
  - class: DockerRequirement
    dockerPull: spodgi/spodgi
baseCommand: odgi_to_rdf
arguments:
  - --syntax=$(inputs.syntax)
  - $(inputs.odgi)
  - $(inputs.output_name)
inputs:
  - id: syntax
    type: string
  - id: odgi
    type: File
  - id: output_name
    type: string
outputs:
  - id: rdf
    type: File
    outputBinding:
      glob: "$(inputs.output_name)"

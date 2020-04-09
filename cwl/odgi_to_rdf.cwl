#!/usr/bin/env cwl-runner
class: CommandLineTool
cwlVersion: v1.1
hints:
  DockerRequirement:
    dockerPull: spodgi/spodgi
requirements:
  InlineJavascriptRequirement: {}
inputs:
  - id: syntax
    type: string?
    inputBinding:
      prefix: --syntax
      position: 1
  - id: odgi
    type: File
    inputBinding:
      position: 2
  - id: output_name
    type: string?

baseCommand: odgi_to_rdf.py
arguments:
  - valueFrom: $(inputs.output_name || inputs.odgi.nameroot+'.rdf')
    position: 3

outputs:
  - id: rdf
    type: File
    outputBinding:
      glob: $(inputs.output_name || inputs.odgi.nameroot+'.rdf')

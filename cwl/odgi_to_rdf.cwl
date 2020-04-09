#!/usr/bin/env cwl-runner
class: CommandLineTool
cwlVersion: v1.1
hints:
  DockerRequirement:
    dockerPull: spodgi/spodgi
requirements:
  InlineJavascriptRequirement: {}
  ShellCommandRequirement: {}
inputs:
  - id: odgi
    type: File
  - id: output_name
    type: string?

stdout: $(inputs.output_name || inputs.odgi.nameroot+'.ttl.xz')

arguments:
  [odgi_to_rdf.py, $(inputs.odgi), "-",
   {valueFrom: "|", shellQuote: false},
   xz, --stdout]

outputs:
  - id: rdf
    type: stdout

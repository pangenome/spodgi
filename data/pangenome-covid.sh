#!/usr/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )/../covid/"
set -e
source ${DIR}/../env.sh
download=$1
downloadInsdc=$2
modify=$3
baseIri="http://arvados.org/"
collection=lugli-4zz18-z513nlpqm03hpca
if [ $download -eq 1 ];
then
    cd ${DIR}
    # Get the latest odgi from the virtual biohackathon build
    #wget "https://workbench.lugli.arvadosapi.com/collections/lugli-4zz18-z513nlpqm03hpca/readsMergeDedup.ttl.xz" -O -| \
    #  xzcat | \
    #  sed -e 's_http://example.org/vg/path/__g' | \
    #  sed -e 's_http://example.org/vg/_https://workbench.lugli.arvadosapi.com/collections/lugli-4zz18-z513nlpqm03hpca/_g' > "${DIR}/pangenome-covid.ttl"

    wget -N "https://workbench.lugli.arvadosapi.com/collections/${collection}/relabeledSeqs_dedup_relabeledSeqs_dedup.odgi"
    
    wget -N "https://workbench.lugli.arvadosapi.com/collections/${collection}/relabeledSeqs_dedup_relabeledSeqs_dedup.gfa"
    
    wget -N "https://workbench.lugli.arvadosapi.com/collections/${collection}/mergedmetadata.ttl"

fi

if [ 1 -eq $modify ]
then
s="";
for p in $(docker run --mount type=bind,source=/home/jbollema/git/spodgi/covid,target=/covid,rw,z -t docker.io/jerven/odgi paths -L -i /covid/relabeledSeqs_dedup_relabeledSeqs_dedup.odgi|grep -oP "\S+");
do 
    s="$s -e "$(grep $p ${DIR}/mergedmetadata.ttl|grep fasta_label| awk '{print "s|"substr($1,2,(length($1))-2)"|http://identifiers.org/insdc/"substr($3,2,(length($3))-2)"#sequence|g"}')" " ;
done;
s="sed $s"
echo $s
cat ${DIR}/relabeledSeqs_dedup_relabeledSeqs_dedup.gfa | $s > ${DIR}fixedIri.gfa
docker run --mount type=bind,source=/home/jbollema/git/spodgi/covid,target=/covid,rw,z -t docker.io/jerven/odgi:latest build -g /covid/fixedIri.gfa -o /covid//fixedIri.odgi
docker run --mount type=bind,source=/home/jbollema/git/spodgi/covid,target=/covid,rw,z -t docker.io/jerven/spodgi:latest odgi_to_rdf.py --base="$baseIri" /covid/fixedIri.odgi "/covid/pangenome-covid.ttl"

grep -v 'http://purl.obolibrary.org/obo/NCIT_C42781' "${DIR}/mergedmetadata.ttl" > "${DIR}/pangenome-metadata.ttl"

grep "http://purl.obolibrary.org/obo/NCIT_C42781" "${DIR}/mergedmetadata.ttl" | \
    sed -e 's_.;_.","_g' | \
    sed -e 's_,_, _g' >> "${DIR}/pangenome-metadata.ttl" 

    #baseIri="https://graph-genome.github.io/SARS2-CoV2-genbank/$(date --iso)/"
    # Covert this to basic rdf ntriples
    #${DIR}/../odgi_to_rdf.py --base "$baseIri" ${DIR}/pangenome-covid.odgi ${DIR}/pangenome-covid.nt

    #curl "https://workbench.lugli.arvadosapi.com/collections/1d61bf7c5d000d5e51e41e2f10e2896d+408/readsMergeDedup.ttl.xz?disposition=attachment&size=8748" | unxz > ${DIR}/pangenome-covid.nt

    # Lets start fixing IRI's and making somewhat nice turtle
    cat <(echo "@base <$baseIri> .") \
        <(echo "@prefix vg: <http://biohackathon.org/resource/vg#> .") \
        <(echo "@prefix f2f: <http://biohackathon.org/resource/vg#linksForwardToForward> .") \
        <(echo "@prefix N: <http://biohackathon.org/resource/vg#Node> .") \
        <(echo "@prefix l: <http://biohackathon.org/resource/vg#links> .") \
        <(echo "@prefix v: <http://www.w3.org/1999/02/22-rdf-syntax-ns#value> .") \
        <(echo "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .") \
        <(echo "@prefix faldo: <http://biohackathon.org/resource/faldo#> .") \
        <(echo "@prefix EP: <http://biohackathon.org/resource/faldo#ExactPosition> .") \
        <(echo "@prefix i: <http://identifiers.org/indsc/> .") \
        <(echo "@prefix s: <http://www.w3.org/2004/02/skos/core#> .") \
        <(echo "@prefix owl: <http://www.w3.org/2002/07/owl#> .") \
        <(echo "@prefix P: <http://biohackathon.org/resource/faldo#Position> .") \
        ${DIR}/pangenome-covid.ttl | \
        riot --syntax=turtle --output=turtle --base "$baseIri" > ${DIR}/pangenome-covid-nice.ttl
        #rapper -i turtle -I "$baseIri" -o turtle - \
fi

if [ $downloadInsdc -eq 1 ]
then
    cd $DIR
    mkdir -p insdc
    cd insdc

    # One wget invocation saves a lot of time because of reusing the http connection
    #We look for identifiers in the pangenome file to hook onto
    
    for label in $(grep "http://biohackathon.org/bh20-seq-schema/original_fasta_label" "${DIR}/pangenome-metadata.ttl"  | \
        cut -f 2 -d '"' | \
        grep -oP "^\w+\.\d+" | \
        sort -u)
    do
        curl  --etag-compare $label.etag \
              --etag-save $label.etag \
              "http://togows.org/entry/nucleotide/$label.ttl" -o $label.ttl
    done
fi
cd $DIR

if [ 1 -eq $modify ]
then 
#Concatenate all these INSDC ttl files into one
echo "Gathering all INSDC files"
rapper -i turtle -o turtle <(cat <(echo '@prefix i: <http://identifiers.org/insdc/> .') $DIR/insdc/*.ttl) > $DIR/insdc.ttl

echo "Adding owl:sameAs and skos:closeMatch"
echo "@prefix skos: <http://www.w3.org/2004/02/skos/core#> ." >> "${DIR}/pangenome-covid-nice.ttl"
echo "@prefix owl: <http://www.w3.org/2002/07/owl#> ." >> "${DIR}/pangenome-covid-nice.ttl"
grep "http://biohackathon.org/bh20-seq-schema/original_fasta_label" "${DIR}/pangenome-metadata.ttl" | sed -e 's|<http://biohackathon.org/bh20-seq-schema/original_fasta_label>|skos:closeMatch|g' | sed -E 's|\"([A-Z0-9]+.[0-9]+)\"|<http://identifiers.org/insdc/\1#sequence>|g' >> "${DIR}/pangenome-covid-nice.ttl"

grep "http://biohackathon.org/bh20-seq-schema/original_fasta_label" "${DIR}/pangenome-metadata.ttl" | sed -e 's|<http://biohackathon.org/bh20-seq-schema/original_fasta_label>|skos:closeMatch|g' | sed -E 's|\"([A-Z0-9]+).[0-9]+\"|<http://purl.uniprot.org/embl/\1>|g' >> "${DIR}/pangenome-covid-nice.ttl"

grep "http://biohackathon.org/bh20-seq-schema/original_fasta_label" "${DIR}/pangenome-metadata.ttl" | sed -e 's|<http://biohackathon.org/bh20-seq-schema/original_fasta_label>|skos:closeMatch|g' | sed -E 's|.+ \"([A-Z0-9]+).([0-9]+)\"|<http://purl.uniprot.org/embl/\1> owl:sameAs <http://identifiers.org/insdc/\1.\2#sequence> |g' >> "${DIR}/pangenome-covid-nice.ttl"

grep "http://biohackathon.org/bh20-seq-schema/original_fasta_label" "${DIR}/pangenome-metadata.ttl" | sed -e 's|<http://biohackathon.org/bh20-seq-schema/original_fasta_label>|skos:closeMatch|g' | sed -E 's|.+ \"([A-Z0-9]+).([0-9]+)\"|<http://identifiers.org/insdc/\1.\2#sequence> owl:sameAs <http://purl.uniprot.org/embl/\1> |g' >> "${DIR}/pangenome-covid-nice.ttl"

fi

echo "Concatentate into one and do a basic compression step"

cat \
    <(echo "@prefix vg: <http://biohackathon.org/resource/vg#> .") \
    <(echo "@prefix f2f: <http://biohackathon.org/resource/vg#linksForwardToForward> .") \
    <(echo "@prefix N: <http://biohackathon.org/resource/vg#Node> .") \
    <(echo "@prefix l: <http://biohackathon.org/resource/vg#links> .") \
    <(echo "@prefix v: <http://www.w3.org/1999/02/22-rdf-syntax-ns#value> .") \
    <(echo "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .") \
    <(echo "@prefix faldo: <http://biohackathon.org/resource/faldo#> .") \
    <(echo "@prefix EP: <http://biohackathon.org/resource/faldo#ExactPosition> .") \
    <(echo "@prefix i: <http://identifiers.org/indsc/> .") \
    <(echo "@prefix s: <http://www.w3.org/2004/02/skos/core#> .") \
    <(echo "@prefix owl: <http://www.w3.org/2002/07/owl#> .") \
    <(echo "@prefix P: <http://biohackathon.org/resource/faldo#Position> .") \
    <(echo "@prefix EP: <http://biohackathon.org/resource/faldo#ExactPosition> .") \
    <(echo "@prefix i: <http://identifiers.org/indsc/> .") \
    <(echo "@prefix s: <http://www.w3.org/2004/02/skos/core#> .") \
    <(echo "@prefix owl: <http://www.w3.org/2002/07/owl#> .") > $DIR/pangenome-covid-all.ttl
riot --syntax=turtle --output=turtle --base "$baseIri"  \
       <(cat $DIR/insdc.ttl $DIR/pangenome-covid-nice.ttl $DIR/pangenome-metadata.ttl) | \
 grep -v "^$" | \
 sed 's/vg:linksForwardToForward/f2f:/g' | \
 sed 's/vg:Node/N:/g' | \
 sed 's/vg:links/l:/g' | \
 sed 's/faldo:ExactPosition/EP:/g' | \
 sed 's/faldo:Position/P:/g' | \
 sed 's/rdf:value/v:/g' \
 >> $DIR/pangenome-covid-all.ttl 
cp $DIR/pangenome-covid-all.ttl $DIR/$(date --iso|tr -d '-').ttl


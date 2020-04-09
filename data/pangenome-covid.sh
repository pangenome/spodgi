#!/usr/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${DIR}/../env.sh

# Get the latest odgi from the virtual biohackathon build
wget "https://workbench.lugli.arvadosapi.com/collections/ed4277a320bd66fc1527142a9ad9ac2e+284/readsMergeDedup.odgi?disposition=attachment&size=601574" -O ${DIR}pangenome-covid.odgi

baseIri="https://graph-genome.github.io/SARS2-CoV2-genbank/$(date --iso)/"

# Covert this to basic rdf ntriples
${DIR}/../odgi_to_rdf.py --base "$baseIri" ${DIR}/pangenome-covid.odgi ${DIR}/pangenome-covid.nt

# Lets start fixing IRI's and making somewhat nice turtle
cat <(echo -e  "@base <$baseIri> .") \
 <(echo "@prefix vg: <http://biohackathon.org/resource/vg#> .") \
 <(echo "@prefix f2f: <http://biohackathon.org/resource/vg#linksForwardToForward> .") \
 <(echo "@prefix N: <http://biohackathon.org/resource/vg#Node> .") \
 <(echo "@prefix l: <http://biohackathon.org/resource/vg#links> .") \
 <(echo "@prefix v: <http://www.w3.org/1999/02/22-rdf-syntax-ns#value> .") \
 <(echo "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .") \
 <(echo "@prefix faldo: <http://biohackathon.org/resource/faldo#> .") \
 <(echo "@prefix EP: <http://biohackathon.org/resource/faldo#ExactPosition> .") \
 <(echo "@prefix i: <http://identifiers.org/indsc/> .") \
 <(echo "@prefix owl: <http://www.w3.org/2002/07/owl#> .") \
 <(echo "@prefix P: <http://biohackathon.org/resource/faldo#Position> .") \
 ${DIR}/pangenome-covid.nt | rapper -i turtle -I "$baseIri" -o turtle - \
 > ${DIR}/pangenome-covid.ttl

cd $DIR
mkdir -p insdc
cd insdc
# One wget invocation saves a lot of time because of reusing the http connection
# We look for identifiers in the pangenome file to hook onto
wget -c -i <(grep -P "^<path\/[A-Z_0-9]+\/" $DIR/pangenome-covid.ttl | \
             cut -f 2 -d '/' | \
             sort -u | \
             xargs -I '{}' -exec echo "http://togows.org/entry/nucleotide/{}.ttl")
cd $DIR

#Concatenate all these INSDC ttl files into one
echo "@prefix : <$baseIri> . " > $DIR/insdc.ttl
rapper -i turtle -o turtle <(cat $DIR/insdc/*.ttl) >> $DIR/insdc.ttl

forsed=""
# Replace path IRIs with INSDC IRIs 
# Also add owl:sameAs to some uniprot/embl IRIs
for path in $(grep -P "^<path\/[A-Z_0-9]+\/" $DIR/pangenome-covid.ttl | \
             cut -f 2 -d '/' | \
             sort -u )
do
    echo $path
    sequence=$(grep -m 1 -oP "$path\.\d+#sequence" $DIR/insdc.ttl)
    forsed="$forsed -e 's|path/${path}|http://identifiers.org/insdc/${sequence}|g'"
    echo "<http://identifiers.org/insdc/$sequence> owl:sameAs <http://purl.uniprot.org/embl/$path> ." >> $DIR/pangenome-covid.ttl

    echo "<http://purl.uniprot.org/embl/$path> owl:sameAs <http://identifiers.org/insdc/$sequence> ." >> $DIR/pangenome-covid.ttl
done

# Run one sed invocation instead of lots with
echo $forsed
conv="cat $DIR/pangenome-covid.ttl | sed $forsed > $DIR/pangenome-covid.ttl.test"
eval $conv
mv $DIR/pangenome-covid.ttl.test $DIR/pangenome-covid.ttl


# Concatentate into one and do a basic compression step
rapper -i turtle \
       -o turtle \
       -I "http://identifiers.org/insdc/" \
       <(cat $DIR/insdc.ttl $DIR/pangenome-covid.ttl) | \
 grep -v "^$" | \
 sed 's/vg:linksForwardToForward/f2f:/g' | \
 sed 's/vg:Node/N:/g' | \
 sed 's/vg:links/l:/g' | \
 sed 's/faldo:ExactPosition/EP:/g' | \
 sed 's/faldo:Position/P:/g' | \
 sed 's/rdf:value/v:/g' \
 > $DIR/$(date --iso|tr -d '-').ttl

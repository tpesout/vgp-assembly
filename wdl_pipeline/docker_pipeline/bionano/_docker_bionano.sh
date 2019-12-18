#!/bin/bash

module load repeatmasker
RepeatMasker -v
module load repeatmasker/4.0.7
RepeatMasker -v
echo "Running repeatmasker on refEcoli.fasta ... (This may take a while)"
wget https://users.soe.ucsc.edu/~tpesout/data/refEcoli.fasta
RepeatMasker -pa 4 refEcoli.fasta
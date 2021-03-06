#!/bin/sh

name=$1
out=$2

bam=$name.bam
bed=$name.bed

if [ -z $name ]; then
	echo "Usage: ./salsa2.sh <name>"
	echo -e "\tSymlink re_sites.txt"
	exit -1
fi

if ! [ -e $bed ]; then
	module load bedtools
	echo "bedtools bamtobed -i $bam > $bed"
	bedtools bamtobed -i $bam > $bed
fi

source /data/Phillippy/tools/conda/etc/profile.d/conda.sh
conda activate salsa_env

fasta=$1.fasta

enz=`cat re_bases.txt`

mkdir -p $out

echo "\
python /data/Phillippy/tools/salsa2/SALSA/run_pipeline.py -a $fasta -l $fasta.fai -e $enz -b $bed -o $out -m yes -i 5 -p yes"
python /data/Phillippy/tools/salsa2/SALSA/run_pipeline.py -a $fasta -l $fasta.fai -e $enz -b $bed -o $out -m yes -i 5 -p yes

ln -s $out/scaffolds_FINAL.fasta ${fasta/_s2/_s3}
java -jar -Xmx1g /data/Phillippy/tools/vgp-assembly/git/vgp-assembly/pipeline/stats/fastaContigSize.jar ${fasta/_s2/_s3}

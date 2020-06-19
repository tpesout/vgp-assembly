version 1.0

workflow runHifiasm {
    input {
        File maternalKmerReads
        File paternalKmerReads
        File? referenceFasta
        Array[File] hifiReads
        String sampleName
        Int threadCount
        String dockerImage
    }

    call yakKmerCount as matKmer {
            input:
                readFile=maternalKmerReads,
                referenceFasta=referenceFasta,
                sampleName=sampleName,
                threadCount=threadCount,
                dockerImage=dockerImage
    }

    call yakKmerCount as patKmer {
            input:
                readFile=paternalKmerReads,
                referenceFasta=referenceFasta,
                sampleName=sampleName,
                threadCount=threadCount,
                dockerImage=dockerImage
    }

    call hifiasm as hifi {
            input:
                maternalKmers=matKmer.yakFile,
                paternalKmers=patKmer.yakFile,
                hifiReads=hifiReads,
                sampleName=sampleName,
                threadCount=threadCount,
                dockerImage=dockerImage
    }

    output {
            File maternalKmers = matKmer.yakFile
            File paternalKmers = patKmer.yakFile
            File maternalAssembly = hifi.maternalAssembly
            File paternalAssembly = hifi.paternalAssembly
    }
}

task yakKmerCount {
    input {
        File readFile
        File? referenceFasta
        String sampleName
        Int threadCount
        Int memoryGigabyte=1
        String dockerImage
    }

	command <<<
        # initialize modules
        source /usr/local/Modules/init/bash
        module use /root/modules/
        # Set the exit code of a pipeline to that of the rightmost command
        # to exit with a non-zero status, or zero if all commands of the pipeline exit
        set -o pipefail
        # cause a bash script to exit immediately when a command fails
        set -e
        # cause the bash shell to treat unset variables as an error and exit immediately
        set -u
        # echo each line of the script to stdout so we can see what is happening
        # to turn off echo do 'set +o xtrace'
        set -o xtrace

        if [[ ~{readFile} =~ .*f(ast)?q\.gz$ ]] ; then
            zcat ~{readFile} | yak count -t15 -b37 -o ~{sampleName}.yak
        elif [[ ~{readFile} =~ .*f(ast)?q$ ]] ; then
            cat ~{readFile} | yak count -t15 -b37 -o ~{sampleName}.yak
        elif [[ ~{readFile} =~ .*cram$ ]] ; then
            samtools fastq --reference ~{referenceFasta} ~{readFile} | yak count -t15 -b37 -o ~{sampleName}.yak
        else
            echo "UNSUPPORTED READ FORMAT (expect .fq .fastq .fq.gz .fastq.gz .cram): $(basename ~{readFile}"
            exit 1
        fi

	>>>
	output {
	    File yakFile = sampleName + ".yak"
	}
    runtime {
        cpu: threadCount
        memory: memoryGigabyte + " GB"
        docker: dockerImage
    }
}

task hifiasm {
    input {
        File maternalKmers
        File paternalKmers
        Array[File] hifiReads
        String sampleName
        Int threadCount
        Int memoryGigabyte=200
        String dockerImage
    }

	command <<<
        # initialize modules
        source /usr/local/Modules/init/bash
        module use /root/modules/
        # Set the exit code of a pipeline to that of the rightmost command
        # to exit with a non-zero status, or zero if all commands of the pipeline exit
        set -o pipefail
        # cause a bash script to exit immediately when a command fails
        set -e
        # cause the bash shell to treat unset variables as an error and exit immediately
        set -u
        # echo each line of the script to stdout so we can see what is happening
        # to turn off echo do 'set +o xtrace'
        set -o xtrace

        ln -s ~{maternalKmers} mat.yak
        ln -s ~{paternalKmers} pat.yak

        # run trio hifiasm
        hifiasm -o ~{sampleName} -t~{threadCount} -1 pat.yak -2 mat.yak ~{sep=" " hifiReads}

        # Convert contig GFA to FASTA
        gfatools gfa2fa ~{sampleName}.hap1.p_ctg.gfa > ~{sampleName}.pat.fasta
        gfatools gfa2fa ~{sampleName}.hap2.p_ctg.gfa > ~{sampleName}.mat.fasta

	>>>
	output {
	    File maternalAssembly = sampleName + ".mat.fasta"
	    File paternalAssembly = sampleName + ".pat.fasta"
	}
    runtime {
        cpu: threadCount
        memory: memoryGigabyte + " GB"
        docker: dockerImage
    }
}
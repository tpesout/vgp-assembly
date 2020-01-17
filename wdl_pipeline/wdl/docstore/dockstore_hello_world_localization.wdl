version 1.0


workflow HelloWorldLocalization {
    input {
        File FILE
        Array[File] FILES
    }

    call head as single_h {
        input:
            myFile=FILE
    }

    scatter (file in FILES) {
        call extractReads as extractReads_h {
            input:
                readFile=file
        }
    }

    output {
        File fileOut = single_h.myHead
        Array[File] filesOut = extractReads_h.myHead
    }
}

task head {
    input {
        File myFile
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

        head ~{myFile}
        ln -s ~{myFile} mySymlinkFile
        head mySymlinkFile >>output
    >>>
    output {
        File myHead = read_string("output")
    }
    runtime {
        docker: "tpesout/vgp_minimap2:latest"
        cpu: 1
    }

}

task extractReads {
    input {
        File readFile
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

    module load samtools

    filename=$(basename -- "~{readFile}")
    prefix="${filename%.*}"
    suffix="${filename##*.}"

    mkdir output

    if [[ "$suffix" == "bam" ]] ; then
      samtools fastq ~{readFile} > output/${prefix}.fq
    elif [[ "$suffix" == "gz" ]] ; then
      gunzip -k -c ~{readFile} > output/${prefix}
    elif [[ "$suffix" != "fastq" ]] && [[ "$suffix" != "fq" ]] && [[ "$suffix" != "fasta" ]] && [[ "$suffix" != "fa" ]] ; then
      echo "Unsupported file type: ${suffix}"
      exit 1
    fi
	>>>

    output {
        File outputFile = flatten([glob("output/*"), [readFile]])[0]
    }

    runtime {
        docker: "tpesout/vgp_base:latest"
        cpu: 1
    }
}

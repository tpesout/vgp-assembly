import "shasta.wdl" as shasta
import "minimap2.wdl" as minimap2
import "marginPolish.wdl" as marginPolish
import "purge_dups.wdl" as purgeDups
import "scaff10x.wdl" as scaff10x
import "busco.wdl" as busco
import "stats.wdl" as stats

workflow ONTAssembly {
    Array[File] READ_FILES_ONT
    Array[File] READ_FILES_10X
    String SAMPLE_NAME
    File MARGIN_POLISH_PARAMS
    Int EXPECTED_GENOME_SIZE
    Int THREAD_COUNT
    Int MEMORY_GB

    # actual work
    call shasta.shasta as shastaAssemble {
        input:
            readFilesONT=READ_FILES_ONT,
            sampleName=SAMPLE_NAME,
            threadCount=THREAD_COUNT,
            memoryGigabyte=MEMORY_GB
    }
	call minimap2.minimap2 as shastaAlign {
	    input:
            refFasta=shastaAssemble.assemblyFasta,
            readFiles=READ_FILES_ONT,
            minimapPreset="map-ont",
            samtoolsFilter="-F 0x904"
	}
	call marginPolish.marginPolish as shastaMarginPolish {
	    input:
            sampleName=SAMPLE_NAME,
            alignmentBam=shastaAlign.minimap2Bam,
            alignmentBamIdx=shastaAlign.minimap2BamIdx,
            referenceFasta=shastaAssemble.assemblyFasta,
            parameters=MARGIN_POLISH_PARAMS,
            featureType="",
            threadCount=THREAD_COUNT,
            memoryGigabyte=MEMORY_GB
	}
    call purgeDups.purge_dups as polishedPurgeDups {
        input:
            assemblyFasta=shastaMarginPolish.polishedFasta,
            readFiles=READ_FILES_ONT,
            minimapPreset="map-ont",
            sampleName=SAMPLE_NAME,
            threadCount=THREAD_COUNT,
            memoryGigabyte=MEMORY_GB
    }
    call scaff10x.scaff10x as scaff10xPolishedPurged {
        input:
            assemblyFasta=polishedPurgeDups.primary,
            readFiles=READ_FILES_10X,
            sampleName=SAMPLE_NAME,
            threadCount=THREAD_COUNT,
            memoryGigabyte=MEMORY_GB
    }
    

	### stats and validation
	# asm stats
	call stats.stats as shastaStats {
	    input:
	        assemblyFasta=shastaAssemble.assemblyFasta,
	        expectedGenomeSize=EXPECTED_GENOME_SIZE
	}
	call stats.stats as marginPolishStats {
	    input:
	        assemblyFasta=shastaMarginPolish.polishedFasta,
	        expectedGenomeSize=EXPECTED_GENOME_SIZE
	}
	call stats.stats as purgedPolishedPriStats {
	    input:
	        assemblyFasta=polishedPurgeDups.primary,
	        expectedGenomeSize=EXPECTED_GENOME_SIZE
	}
	call stats.stats as purgedPolishedAltStats {
	    input:
	        assemblyFasta=polishedPurgeDups.alternate,
	        expectedGenomeSize=EXPECTED_GENOME_SIZE
	}
	call stats.stats as scaffoldedPurgedPolishedStats {
	    input:
	        assemblyFasta=scaff10xPolishedPurged.scaffoldedFasta,
	        expectedGenomeSize=EXPECTED_GENOME_SIZE
	}
	# busco stats
	call busco.busco as shastaBusco {
	    input:
	        assemblyFasta=shastaAssemble.assemblyFasta
	}
	call busco.busco as marginPolishBusco {
	    input:
	        assemblyFasta=shastaMarginPolish.polishedFasta
	}
	call busco.busco as scaffoldedPolishedPurgedBusco {
	    input:
	        assemblyFasta=scaff10xPolishedPurged.scaffoldedFasta
	}

	output {
		File shastaAssembly = shastaAssemble.assemblyFasta
		File marginPolishAssembly = shastaMarginPolish.polishedFasta
		File polishedPurgedHaplotype = polishedPurgeDups.primary
		File polishedPurgedAlternate = polishedPurgeDups.alternate
		File scaffoldedPolishedPurgedFasta = scaff10xPolishedPurged.scaffoldedFasta

        # validation
		File shastaBuscoResult = shastaBusco.outputTarball
		File polishedBuscoResult = marginPolishBusco.outputTarball
		File polishedPurgedScaffoldedBuscoResult = scaffoldedPolishedPurgedBusco.outputTarball

		File shastaStatsResult = shastaStats.statsTarball
		File marginPolishStatsResult = marginPolishStats.statsTarball
		File purgedPolishedHaplotypeStatsResult = purgedPolishedPriStats.statsTarball
		File purgedPolishedAlternateStatsResult = purgedPolishedAltStats.statsTarball
		File scaffoldedPurgedPolishedStatsResult = scaffoldedPurgedPolishedStats.statsTarball
	}
}

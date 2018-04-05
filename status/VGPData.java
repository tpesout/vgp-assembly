import java.util.ArrayList;

public class VGPData {

	private String speciesId;
	private String speciesName;
	
	private int numSubreadBams = 0;
	private int numScrapsBams = 0;
	private int num10xR1 = 0;
	
	private boolean bspqi = false;
	private boolean bsssi = false;
	private boolean tgh = false;
	private boolean dls = false;
	private boolean hasBnx = false;
	private boolean hasCmap = false;
	ArrayList<String> hicVenders = new ArrayList<String>();
	
	public VGPData(String speciesId, String speciesName) {
		this.speciesId = speciesId;
		this.speciesName = speciesName;
	}
	
	public void addPacbio(String file) {
		if (file.contains("subread")) {
			numSubreadBams++;
		} else if (file.contains("scraps")) {
			numScrapsBams++;
		}
	}
	
	public void add10xR1(String file) {
		if (file.contains("r1")) {
			num10xR1++;
		}
	}
	
	public void addHiC(String vendor) {
		if (!hicVenders.contains(vendor)) {
			hicVenders.add(vendor);
		}
	}
	
	public void addBionano(String file) {
		if (file.contains("bspqi")) {
			bspqi = true;
		} else if (file.contains("bsssi")) {
			bsssi = true;
		} else if (file.contains("dle") || file.contains("dls")) {
			dls = true;
		}
		
		if (file.contains("bnx")) {
			hasBnx = true;
		} else if (file.contains("cmap")) {
			hasCmap = true;
		}
	}
	
	public void printVGPData(boolean isMDstyle) {
		if (bspqi && bsssi) {
			tgh = true;
		}
		
		if (isMDstyle) {
			System.out.println("| " + speciesName + "\t" +
					"| " + speciesId + "\t" +
					"| " + numSubreadBams + "\t" + 
					"| " + numScrapsBams + "\t" +
					"| " + num10xR1 + "\t" +
					"| " + (tgh ? "O" : "X") + "\t" +
					"| " + (dls ? "O" : "X") + "\t" +
					"| " + (hasBnx ? "O" : "X") + "\t" +
					"| " + (hasCmap ? "O" : "X") + "\t" +
					"| " + listHiC() + " |");
		} else {
			System.out.println(speciesName + "\t" +
					speciesId + "\t" +
					numSubreadBams + "\t" + 
					numScrapsBams + "\t" +
					num10xR1 + "\t" +
					(tgh ? "O" : "X") + "\t" +
					(dls ? "O" : "X") + "\t" +
					(hasBnx ? "O" : "X") + "\t" +
					(hasCmap ? "O" : "X") + "\t" +
					listHiC());
		}
	}
	
	public static void printHeader(boolean isMDstyle) {
		if (isMDstyle) {
			System.out.println("| species_name\t"
					+ "| species_id\t"
					+ "| pacbio_subreads\t"
					+ "| pacbio_scrubs\t"
					+ "| 10x\t"
					+ "| bionano_tgh\t"
					+ "| bionano_dls\t"
					+ "| bionano_bnx\t"
					+ "| bionano_cmap\t"
					+ "| hic |");
			System.out.println("| :---------- | :---------- | :---------- | :---------- | :----- | :----- | :----- | :----- | :----- | :----- |");
		} else {
			System.out.println("species_name\tspecies_id\t"
					+ "pacbio_subreads\tpacbio_scrubs\t10x\t"
					+ "bionano_tgh\tbionano_dls\tbionano_bnx\tbionano_cmap\t"
					+ "hic");
		}
	}
	
	private String listHiC() {
		String vendors = "";
		for(String hiC : hicVenders) {
			vendors += hiC + ",";
		}
		if (!vendors.equals("")) {
			vendors = vendors.substring(0, vendors.length() - 1);
		}
		return vendors;
	}
}
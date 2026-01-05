import xml.etree.ElementTree as ET
import csv
import re

# --- Notes ---
'''
This script parses XML output from FetchAuthorBib.py as its input and then creates a filtered dataset based on the results. 
 The filters subset to entries in the input file that: 1) has the HasPMC=False attribute and 2) has at least one author who has an
 NIH affiliation.
 The output is a four column csv file with the following features: Article,Title,Year,DOI,PMID

Last Updated: 1/5/2026
'''

# --- Config ---
INPUT_XML = "pm-authors.xml"
OUTPUT_CSV = "irp-articles.csv"

# --- NIH Affliation Filter ---
''' 
I initially tried filtering by using the XML grant tag with value "ImNIH" but
 that was massively inconsistent. Instead, I added this much more greedy (and computationally intensive)
 regex based on any NIH IC affiliation listed by at least one of the authors.
 This is still not perfect because it could match to a non-IRP author (even though it's gauranteed that at 
 least 1 author is from the NIH IRP given the source data). 
'''

NIH_KEYWORDS = [
    # General
    "national institutes of health", "nih", "intramural research program",
    
    # Institutes (Full names and Acronyms)
    "national cancer institute", "nci",
    "national eye institute", "nei",
    "national heart, lung, and blood institute", "nhlbi",
    "national human genome research institute", "nhgri",
    "national institute on aging", "nia",
    "national institute on alcohol abuse and alcoholism", "niaaa",
    "national institute of allergy and infectious diseases", "niaid",
    "national institute of arthritis and musculoskeletal and skin diseases", "niams",
    "national institute of biomedical imaging and bioengineering", "nibib",
    "national institute of child health and human development", "nichd", "eunice kennedy shriver",
    "national institute on deafness and other communication disorders", "nidcd",
    "national institute of dental and craniofacial research", "nidcr",
    "national institute of diabetes and digestive and kidney diseases", "niddk",
    "national institute on drug abuse", "nida",
    "national institute of environmental health sciences", "niehs",
    "national institute of general medical sciences", "nigms",
    "national institute of mental health", "nimh",
    "national institute on minority health and health disparities", "nimhd",
    "national institute of neurological disorders and stroke", "ninds",
    "national institute of nursing research", "ninr",
    "national library of medicine", "nlm",
    
    # Centers
    "clinical center", "cc", 
    "center for information technology", "cit",
    "center for scientific review", "csr",
    "fogarty international center", "fic",
    "national center for advancing translational sciences", "ncats",
    "national center for complementary and integrative health", "nccih"
]

# Calling the regex globally a single time should help with runtime/overhead
# \b ensures we match "nia" as a word, but not inside "California".
pattern_string = r'\b(?:' + '|'.join(re.escape(k) for k in NIH_KEYWORDS) + r')\b'
NIH_REGEX = re.compile(pattern_string, re.IGNORECASE)

def is_nih_affiliated(affiliations_list):
    """
    Input: A list of affiliation strings for a single article.
    Output: True if at least one affiliation belongs to the NIH.
    """
    if not affiliations_list:
        return False
        
    for affiliation in affiliations_list:
        if not affiliation: 
            continue
            
        # Check against our compiled regex
        if NIH_REGEX.search(str(affiliation)):
            return True
            
    return False

def extract_year(article_element):
    """
    Helper to safely extract the publication year.
    Checks standard <Year> tag first, falls back to <MedlineDate>.
    """
    pub_date = article_element.find(".//Journal/JournalIssue/PubDate")
    if pub_date is None:
        return "N/A"
        
    year_node = pub_date.find("Year")
    if year_node is not None:
        return year_node.text
    
    # Fallback: Sometimes dates are stored as "2023 Oct-Dec" in MedlineDate
    medline_node = pub_date.find("MedlineDate")
    if medline_node is not None:
        match = re.search(r'\d{4}', medline_node.text)
        if match:
            return match.group(0)
            
    return "N/A"

def main():
    print(f"Parsing {INPUT_XML}...")
    
    try:
        # Load the XML tree
        tree = ET.parse(INPUT_XML)
        root = tree.getroot()
        
        matches = []
        
        # Iterate through every article in the set
        for article in root.findall(".//PubmedArticle"):
            
            # --- FILTER 1: Check HasPMC Tag ---
            # We look for the custom tag we added in the previous script
            has_pmc = article.find("HasPMC")
            if has_pmc is None or has_pmc.text != "False":
                continue # Skip if it has PMC or tag is missing
                
            # --- FILTER 2: Check for NIH Affiliation ---
            # Extract all affiliation strings from this article
            # Using .//Affiliation ensures we catch them wherever they are nested in AuthorList
            article_affiliations = [
                aff.text for aff in article.findall(".//Affiliation") 
                if aff.text is not None
            ]
            
            # Pass the list to our helper function
            if not is_nih_affiliated(article_affiliations):
                continue # Skip if no NIH affiliation is found
            
            # --- EXTRACTION ---
            
            # 1. Title
            title_node = article.find(".//ArticleTitle")
            title = title_node.text if title_node is not None else "No Title"
            
            # 2. Year
            year = extract_year(article)
            
            # 3. DOI (with Prefix)
            doi_node = article.find(".//ArticleId[@IdType='doi']")
            if doi_node is not None:
                doi_link = f"https://www.doi.org/{doi_node.text}"
            else:
                doi_link = "N/A"
                
            # 4. PMID (with Prefix)
            pmid_node = article.find(".//ArticleId[@IdType='pubmed']")
            if pmid_node is not None:
                pmid_link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid_node.text}"
            else:
                pmid_link = "N/A"
                
            matches.append([title, year, doi_link, pmid_link])
            
        # --- WRITE TO CSV ---
        if matches:
            with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Header
                writer.writerow(["Article Title", "Year", "DOI", "PMID"])
                # Data
                writer.writerows(matches)
            
            print(f"Success! Found {len(matches)} articles matching criteria.")
            print(f"Saved to: {OUTPUT_CSV}")
        else:
            print("No articles found matching filters.")

    except FileNotFoundError:
        print(f"  Error: Could not find input file '{INPUT_XML}'")
    except ET.ParseError:
        print(f"  Error: '{INPUT_XML}' is not valid XML.")

if __name__ == "__main__":
    main()

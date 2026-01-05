import requests
import csv
import time
import xml.etree.ElementTree as ET

# --- Notes ---
''' 
 I wrote this based on years-old code. 
 There may be a more up-to-date and efficient way to call NCBI's E-Utils API.
 Last Updated: 1/5/2026
'''

# --- Config ---
API_KEY = ""   # Leave empty if you don't have one (will be rate limited per NCBI). You can get an API Key from your NCBI account (under Account Settings).
EMAIL = "your@email.goes.here"
TOOL_NAME = "FetchAuthorBib"
INPUT_CSV = "authors.csv"
OUTPUT_FILE = "pm-authors.xml"
BATCH_SIZE = 100  # Number of articles to fetch per request (Max 100-200 recommended since there's a high chance of errors)

def get_session():
    s = requests.Session()
    s.headers.update({"User-Agent": f"{TOOL_NAME}/1.0"})
    s.params = {
        "email": EMAIL,
        "tool": TOOL_NAME,
        "api_key": API_KEY
    }
    return s

def process_author(author_name, session, outfile):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    clean_name = author_name.strip().replace('\ufeff', '')
    print(f"Searching for: {clean_name}...")
    
    # --- ESEARCH Calls ---
    search_params = {
        "db": "pubmed",
        "term": f"{clean_name}[au]",
        "usehistory": "y",
        "retmode": "json",
        "mindate": "2020",
        "maxdate": "2026",
        "datetype": "pdat"  # 'pdat' = Publication Date, 'edat' = Date added to DB
    }
    
    try:
        r = session.get(f"{base_url}esearch.fcgi", params=search_params)
        r.raise_for_status()
        
        data = r.json().get('esearchresult', {})
        count = int(data.get('count', '0'))
        
        # FIX: The JSON key is usually "querykey", not "query_key"
        # We try both just to be safe.
        query_key = data.get('querykey') or data.get('query_key')
        webenv = data.get('webenv')
        
        print(f"  - Found {count} articles. (QueryKey: {query_key})")
        
        if count == 0:
            return

        if not query_key or not webenv:
            print(f"  Error: Missing history parameters. querykey={query_key}, webenv={webenv}")
            return

        # --- EFETCH (Batch Loop to connect from ESEARCH results) ---
        for start in range(0, count, BATCH_SIZE):
            print(f"  - Fetching batch {start} to {start + BATCH_SIZE}...")
            
            fetch_params = {
                "db": "pubmed",
                "WebEnv": webenv,
                "query_key": query_key,
                "retstart": start,
                "retmax": BATCH_SIZE,
                "retmode": "xml"
            }
            
            # Request data
            fetch_r = session.get(f"{base_url}efetch.fcgi", params=fetch_params)
            fetch_r.raise_for_status()
            
            # --- XML output formatting ---
            try:
                batch_root = ET.fromstring(fetch_r.content)
                
                for article in batch_root.findall(".//PubmedArticle"):
                    # Check for PMC ID
                    pmc_node = article.find(".//ArticleId[@IdType='pmc']")
                    has_pmc = "True" if pmc_node is not None else "False"
                    
                    # Add custom tag <HasPMC>
                    new_tag = ET.SubElement(article, "HasPMC")
                    new_tag.text = has_pmc
                    
                    # Write to file
                    article_str = ET.tostring(article, encoding='unicode')
                    outfile.write(article_str + "\n")
                    
            except ET.ParseError:
                print("  Error parsing XML batch. Skipping...")

            # Rate limiting
            time.sleep(0.34 if API_KEY else 1.0) 

    except Exception as e:
        print(f"  Error processing {clean_name}: {e}")

def main():
    session = get_session()
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        outfile.write('<?xml version="1.0" encoding="utf-8"?>\n')
        outfile.write('<PubmedArticleSet>\n')
        
        try:
            with open(INPUT_CSV, "r", encoding="utf-8-sig") as csvfile: 
                reader = csv.reader(csvfile)
                for row in reader:
                    if not row: continue
                    fullname = f"{row[0]} {row[1]}".strip()
                    process_author(fullname, session, outfile)
                    
        except FileNotFoundError:
            print(f"Error: Could not find {INPUT_CSV}")
        
        outfile.write('</PubmedArticleSet>')
    
    print(f"\nDone! Aggregated results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

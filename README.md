# nih-irb-bib
This repository stores code for extracting and processing scientific article citations by NIH Intramural Research Program (IRP) Principal Investigators from PubMed.
The IRP lists all principal investigators here: https://irp.nih.gov/our-research/principal-investigators/name. 

# Manifest
[code/](code/)
- FetchAuthorBib.py : This script takes a two-column csv with lastname, firstname of a set of authors and then iteratively calls NCBI's E-Utilities API to retreive PubMed entries found with each author's name. The file outputs either xml or json depending on tuning with all retrieved entries. The script attempts to infer whether or not a particular entry has a corresponding "free" article entry in PubMed Central (adding a HasPMC=True tag if found, False otherwise). Additional search parameters, API endpoints, and filters, can be added (see script). Warning: this script can result in very large output files (easily exceeding 1GB).
- ExtractIRPBib.py : This script filters the xml file output from FetchAuthorBib.py retunring a four column csv with bibliometric data for entries that HasPMC=False and where at least one author has an NIH affiliation.

[data/](data/)
- authors.csv : This is a two column csv file storing lastname, firstname of NIH IRP Principal Investigators.
- potential-irp-articles.csv :  The output of ExtractIRPBib.py after running FetchAuthorBib.py on authors.csv. The parameters in FetchAuthorBib.py limited the search for aricles published between 2020 and 2026. 

# How-to-use
1) I strongly recommend obtaining an API-Key from NCBI before running FetchAuthBib.py. You can do that be creating an account with [NCBI](https://pubmed.ncbi.nlm.nih.gov/) and then navigating to "Account Settings". The option generate an API-Key will be at the bottom of the screen.
2) Edit FetchAuthor.py to use your specific credentials, author source file name, and desired output file name.
3) Run FetchAuthor.py
4) Edit ExtractIRPBib.py to fit your specific filenames per (2).


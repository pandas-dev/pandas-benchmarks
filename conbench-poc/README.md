# Conbench PoC for pandas


The **purpose** of adding conbench to the current pandas benchmark system 
is:
1. To improve the UI.
2. Use conbench statistical analysis and detection of regression/improvement
3. Add an automatic alert system for  regressions or improvements.

## Files description
**client.py:** Calls the adapter asvbench.py and posts to a conbench web app. <br/>
**asvbench.py:** Converts asv's benchmarks results to conbench format. <br/>
**alert.py:** Runs conbench alert pipeline, generates a report and sends alerts. <br/>
**benchmark_email.py:** Handles the email. <br/>
**utilities.py:** setup env variables, reads files. <br/>
**setup_server.txt:** Steps to install this PoC. <br/>

## PoC structure/setup
![Setup](setup_pic.png "Setup")
# Covid-19-tracker-india
This is a covid-19 dashboard that tracks corona virus spread in india.

The data has been fetched from Ministry of Health and Family welfare and is publicly available. <br>
PR's suggestions features and improvements are extremely welcome.<br>

Setup Instructions;
```bash
git clone https://github.com/vcode11/Covid-19-tracker-india.git
cd Covid-19-tracker-india
python3 -m venv venv
. venv/bin/activate  
#Activate the virutal environment
pip install -r requirements.txt
echo FLASK_APP=dashboard.py > .flaskenv
# run the server
flask run 
```

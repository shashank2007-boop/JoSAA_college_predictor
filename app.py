from flask import Flask, render_template, request
import pandas as pd
import os

app = Flask(__name__)

try:
    df = pd.read_csv("josaa_2025_cutoffs.csv")
except FileNotFoundError:
    print("WARNING: josaa_2025_cutoffs.csv not found! Make sure it is in the same folder as app.py")
    df = pd.DataFrame() 

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html', result_table=None)

@app.route('/predict', methods=['POST'])
def predict():
    if df.empty:
        return render_template('index.html', result_table="<p class='text-danger text-center'>Database not found. Please add the CSV file.</p>")

    try:
        # 1. Grab inputs from the HTML form
        user_exam = request.form.get('exam_type')
        user_rank = int(request.form.get('rank'))
        user_category = request.form.get('category')
        gender_pool = request.form.get('gender')

        if user_rank <= 0:
            return render_template('index.html', result_table="<p class='text-danger text-center'>Please enter a valid positive integer for rank.</p>")

        # 2. Filter 1: Isolate by Exam Type (IITs vs Non-IITs)
        is_iit = df['Institute'].str.contains("Indian Institute of Technology", na=False, case=False)
        
        if user_exam == "JEE Advanced":
            filtered_df = df[is_iit]
        else:
            filtered_df = df[~is_iit]
        
        # 3. Filter 2: Match the Category
        filtered_df = filtered_df[filtered_df['Category'] == user_category]
        
        # 4. Filter 3: Match the Gender Pool Logic
        if gender_pool == 'Female-only (including Supernumerary)':
            filtered_df = filtered_df[filtered_df['Gender'].isin(['Gender-Neutral', 'Female-only (including Supernumerary)'])]
        else:
            filtered_df = filtered_df[filtered_df['Gender'] == 'Gender-Neutral']

        # 5. Clean Data types: Force ranks to be numeric to safely process
        filtered_df['Opening Rank'] = pd.to_numeric(filtered_df['Opening Rank'], errors='coerce')
        filtered_df['Closing Rank'] = pd.to_numeric(filtered_df['Closing Rank'], errors='coerce')

        # 6. Filter 4: Apply Rank Logic (Rank <= Closing Rank)
        matches = filtered_df[filtered_df['Closing Rank'] >= user_rank]
        
        # 7. Dynamic Column Selection based on the chosen Exam Type
        if user_exam == "JEE Main":
            # Include 'Quota' column for JEE Main outputs
            output_cols = ['Institute', 'Branch', 'Quota', 'Gender', 'Opening Rank', 'Closing Rank']
        else:
            # Omit 'Quota' column for JEE Advanced outputs
            output_cols = ['Institute', 'Branch', 'Gender', 'Opening Rank', 'Closing Rank']
            
        results = matches[output_cols].sort_values(by='Opening Rank')
        
        # 8. Render Table
        if results.empty:
            html_table = "<p class='text-danger text-center fw-bold'>No colleges found for this rank and criteria combination.</p>"
        else:
            html_table = results.to_html(classes="table table-bordered table-hover table-striped text-center", justify="center", index=False)
        
        return render_template('index.html', result_table=html_table)

    except Exception as e:
        error_msg = f"<p class='text-danger text-center'>An error occurred: {str(e)}<br>Verify your CSV columns perfectly match the expected keys.</p>"
        return render_template('index.html', result_table=error_msg)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
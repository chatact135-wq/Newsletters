import os
import re
import zipfile
import tempfile
import html
from flask import Flask, request, send_file, render_template
import pandas as pd
from weasyprint import HTML

app = Flask(__name__)

# CSS curly braces must be doubled {{ }} so Python format() ignores them
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
    @page {{ size: A4 landscape; margin: 10mm; }}
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; color: #333; }}
    .header {{ text-align: center; color: #003366; border-bottom: 3px solid #003366; padding-bottom: 10px; margin-bottom: 15px; }}
    .header h2 {{ margin: 5px 0; font-size: 22px; }}
    .header h3 {{ margin: 5px 0; font-size: 16px; font-weight: normal; color: #555; }}
    .header h4 {{ margin: 10px 0 0 0; font-size: 18px; font-weight: bold; background-color: #003366; color: white; display: inline-block; padding: 8px 15px; border-radius: 5px; }}
    table {{ width: 100%; table-layout: fixed; border-collapse: collapse; margin-top: 10px; font-size: 11px; }}
    th, td {{ border: 1px solid #ddd; padding: 8px 5px; text-align: right; vertical-align: top; word-wrap: break-word; overflow-wrap: break-word; word-break: break-word; white-space: pre-wrap; }}
    th {{ background-color: #003366; color: white; font-weight: bold; text-align: center; }}
    tr:nth-child(even) {{ background-color: #f9f9f9; }}
    .center-text {{ text-align: center; direction: ltr; }}
</style>
</head>
<body>
    <div class="header">
        <h2>KHALIFA BIN ZAYED SCHOOL | مدرسة خليفة بن زايد</h2>
        <h3>الخطة الأسبوعية - Weekly Lesson Plan</h3>
        <h4>الصف والشعبة - Class: {class_name}</h4>
    </div>
    <table>
        <tr>
            <th style="width: 9%;">المادة<br>Subject</th>
            <th style="width: 10%;">اسم المعلم<br>Teacher</th>
            <th style="width: 6%;">الصف<br>Class</th>
            <th style="width: 11%;">الاثنين<br>Monday</th>
            <th style="width: 11%;">الثلاثاء<br>Tuesday</th>
            <th style="width: 11%;">الأربعاء<br>Wednesday</th>
            <th style="width: 11%;">الخميس<br>Thursday</th>
            <th style="width: 11%;">الجمعة<br>Friday</th>
            <th style="width: 20%;">نواتج التعلم<br>Learning Objectives</th>
        </tr>
        {rows}
    </table>
</body>
</html>"""

def clean_text(text):
    if pd.isna(text): return '-'
    t = str(text).strip()
    if not t: return '-'
    
    # Fix for cropping: break up ridiculously long unbroken words (like long email/links)
    t = re.sub(r'(\S{40})', r'\1 ', t) 
    t = html.escape(t)
    return t.replace('\n', '<br>')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file uploaded", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    
    if file and file.filename.endswith('.xlsx'):
        try:
            df = pd.read_excel(file)
            df = df.fillna('')
            
            # Dynamically grab the columns just in case of hidden spaces
            col_class = [c for c in df.columns if 'الصف' in c or 'Class' in c][0]
            col_subject = [c for c in df.columns if 'المادة' in c or 'Subject' in c][0]
            col_teacher = [c for c in df.columns if 'Teacher' in c or 'اسم المعلم' in c][0]
            col_mon = [c for c in df.columns if 'Monday' in c or 'الاثنين' in c][0]
            col_tue = [c for c in df.columns if 'Tuesday' in c or 'الثلاثاء' in c][0]
            col_wed = [c for c in df.columns if 'Wednesday' in c or 'الأربعاء' in c][0]
            col_thu = [c for c in df.columns if 'Thursday' in c or 'الخميس' in c][0]
            col_fri = [c for c in df.columns if 'Friday' in c or 'الجمعة' in c][0]
            col_outcomes = [c for c in df.columns if 'Learning' in c or 'نواتج' in c][0]

            # Get unique classes
            all_classes = set()
            for val in df[col_class]:
                parts = re.split(r'[;,]', str(val))
                for p in parts:
                    p_clean = p.strip()
                    if p_clean:
                        all_classes.add(p_clean)
            all_classes = sorted(list(all_classes))

            # Create PDFs in a temporary directory and zip them
            with tempfile.TemporaryDirectory() as temp_dir:
                pdf_files = []
                for cls in all_classes:
                    def contains_class(row_val, target_class):
                        tokens = [t.strip() for t in re.split(r'[;,]', str(row_val)) if t.strip()]
                        return target_class in tokens
                    
                    subset = df[df[col_class].apply(lambda x: contains_class(x, cls))]
                    
                    rows_html = ""
                    for _, row in subset.iterrows():
                        r_html = f"""
                    <tr>
                        <td><strong>{clean_text(row[col_subject])}</strong></td>
                        <td><strong>{clean_text(row[col_teacher])}</strong></td>
                        <td class="center-text">{cls}</td>
                        <td>{clean_text(row[col_mon])}</td>
                        <td>{clean_text(row[col_tue])}</td>
                        <td>{clean_text(row[col_wed])}</td>
                        <td>{clean_text(row[col_thu])}</td>
                        <td>{clean_text(row[col_fri])}</td>
                        <td>{clean_text(row[col_outcomes])}</td>
                    </tr>"""
                        rows_html += r_html
                        
                    final_html = HTML_TEMPLATE.format(class_name=cls, rows=rows_html)
                    safe_name = re.sub(r'[\\/*?:\[\]]', '', cls).replace(' ', '_')
                    pdf_path = os.path.join(temp_dir, f"{safe_name}.pdf")
                    
                    HTML(string=final_html).write_pdf(pdf_path)
                    pdf_files.append(pdf_path)

                # Zip the files
                zip_path = os.path.join(temp_dir, "Weekly_Lesson_Plans.zip")
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for pf in pdf_files:
                        zipf.write(pf, os.path.basename(pf))
                
                # Send the zip to the user
                return send_file(zip_path, as_attachment=True, download_name="Weekly_Lesson_Plans.zip")
        except Exception as e:
            return f"An error occurred: {str(e)}", 500
    
    return "Invalid file format. Please upload an .xlsx file.", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

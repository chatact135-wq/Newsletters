import os
import re
import zipfile
import tempfile
import html
import uuid
from flask import Flask, request, send_file, render_template, redirect
import pandas as pd
from weasyprint import HTML

app = Flask(__name__)
os.makedirs('uploads', exist_ok=True)

# ----------------- MASTER SCHEDULE DATA -----------------
RAW_MASTER = {
    '9 A1': [('Arabic', 'Sohail Kas'), ('Biology', 'Ashish'), ('English', 'Ameer'), ('Islamic', 'Ahmed tha'), ('Math', 'ANZIL MA'), ('Physics', 'Tamir'), ('Social', 'ASHRAF')],
    '9 A2': [('Arabic', 'TAISIER Ar'), ('Biology', 'Ashish'), ('English', 'Ameer'), ('Islamic', 'Ahmed tha'), ('Math', 'ANZIL MA'), ('Physics', 'PRIYA P.'), ('Social', 'ASHRAF')],
    '9 G1': [('Arabic', 'Sohail Kas'), ('Business', 'Alisa'), ('English', 'KELSEY'), ('Islamic', 'Ahmed tha'), ('Math', 'ABDRHMA N KA'), ('Science', 'Mo Muktar'), ('Social', 'Wsam')],
    '9 G2': [('Arabic', 'Sohail Kas'), ('Business', 'Alisa'), ('English', 'Rabea'), ('Islamic', 'Ahmed tha'), ('Math', 'ABDRHMA N KA'), ('Science', 'Mo Muktar'), ('Social', 'Wsam')],
    '9 G3': [('Arabic', 'TAISIER Ar'), ('Business', 'Alisa'), ('English', 'Rabea'), ('Islamic', 'Ahmed tha'), ('Math', 'ABDRHMA N KA'), ('Science', 'PRIYA P.'), ('Social', 'Wsam')],
    '9 G4': [('Arabic', 'TAISIER Ar'), ('Business', 'Alisa'), ('English', 'Jalal'), ('Islamic', 'Ahmed tha'), ('Math', 'ANZIL MA'), ('Science', 'hisham Ahmed'), ('Social', 'ASHRAF')],
    '9 G5': [('Arabic', 'TAISIER Ar'), ('Business', 'Alisa'), ('English', 'Jalal'), ('Islamic', 'Ahmed tha'), ('Math', 'ANZIL MA'), ('Science', 'hisham Ahmed'), ('Social', 'ASHRAF')],
    '10 A1': [('Arabic', 'A Swadha'), ('Chemistry', 'M Graibah'), ('English', 'Rabea'), ('Islamic', 'Sohail sham'), ('Math', 'Moh Krimen'), ('Physics', 'hisham Ahmed'), ('Social', 'HANI Z.')],
    '10 A2': [('Arabic', 'FADI A.'), ('Chemistry', 'M Graibah'), ('English', 'Rabea'), ('Islamic', 'Sohail sham'), ('Math', 'Moh Krimen'), ('Physics', 'hisham Ahmed'), ('Social', 'HANI Z.')],
    '10 G1': [('Arabic', 'Gamal'), ('Business', 'Alisa'), ('English', 'Ameer'), ('Islamic', 'Sohail sham'), ('Math', 'Moh Mohye'), ('Science', 'Tamir'), ('Social', 'HANI Z.')],
    '10 G2': [('Arabic', 'FADI A.'), ('Business', 'Alisa'), ('English', 'Ameer'), ('Islamic', 'Sohail sham'), ('Math', 'Moh Mohye'), ('Science', 'Tamir'), ('Social', 'HANI Z.')],
    '10 G3': [('Arabic', 'A Swadha'), ('Business', 'Alisa'), ('English', 'Rabea'), ('Islamic', 'Sohail sham'), ('Math', 'ABDALLAH'), ('Science', 'Tamir'), ('Social', 'Wsam')],
    '10 G4': [('Arabic', 'A Swadha'), ('Business', 'Alisa'), ('English', 'Rabea'), ('Islamic', 'Sohail sham'), ('Math', 'ABDRHMA N KA'), ('Science', 'Shawkat'), ('Social', 'Wsam')],
    '11 A1': [('Arabic', 'Elsayed'), ('Biology', 'Ashish'), ('Chemistry', 'M Graibah'), ('English', 'Najeh'), ('Health', 'Mushtag'), ('Islamic', 'Ahmed Alshar'), ('Math', 'Moh Mohye'), ('Physics', 'Mo Muktar'), ('Social', 'HANI Z.')],
    '11 A2': [('Arabic', 'Elsayed'), ('Biology', 'Ashish'), ('Chemistry', 'M Graibah'), ('English', 'Najeh'), ('Islamic', 'Ahmed Alshar'), ('Math', 'Moh Mohye'), ('Physics', 'Mo Muktar'), ('Social', 'HANI Z.')],
    '11 G1': [('Arabic', 'Elsayed'), ('Biology', 'Shawkat'), ('Chemistry', 'Eyad'), ('English', 'Kalid E'), ('Islamic', 'Ahmed Alshar'), ('Math', 'WAEL'), ('Social', 'HANI Z.')],
    '11 G2': [('Arabic', 'Elsayed'), ('Biology', 'Shawkat'), ('Chemistry', 'Eyad'), ('English', 'Kalid E'), ('Islamic', 'Ahmed Alshar'), ('Math', 'WAEL'), ('Social', 'HANI Z.')],
    '11 G3': [('Arabic', 'TAISIER Ar'), ('Biology', 'Shawkat'), ('Chemistry', 'Eyad'), ('English', 'Kalid E'), ('Health', 'Mushtag'), ('Islamic', 'Ahmed Alshar'), ('Math', 'WAEL'), ('Social', 'HANI Z.')],
    '12 A1': [('Arabic', 'Elsayed'), ('Biology', 'Ashish'), ('English', 'Najeh'), ('Islamic', 'Ahmed Alshar'), ('Math', 'Mohamed Hafez'), ('Physics', 'Ayman'), ('Social', 'ASHRAF')],
    '12 A2': [('Arabic', 'A Swadha'), ('Biology', 'Ashish'), ('Chemistry', 'Eyad'), ('English', 'Najeh'), ('Health', 'Mushtag'), ('Islamic', 'Ahmed Alshar'), ('Math', 'Mohamed Hafez'), ('Physics', 'Ayman'), ('Social', 'ASHRAF')],
    '12 G1': [('Arabic', 'Gamal'), ('Biology', 'Ashish'), ('Chemistry', 'Eyad'), ('English', 'Jalal'), ('Islamic', 'Ahmed Alshar'), ('Math', 'Mohamed Hafez'), ('Social', 'ASHRAF')],
    '12 G2': [('Arabic', 'Gamal'), ('Biology', 'Ashish'), ('Chemistry', 'Eyad'), ('English', 'Jalal'), ('Islamic', 'Ahmed Alshar'), ('Math', 'ABDALLAH H'), ('Social', 'ASHRAF')],
    '12 G3': [('Arabic', 'Gamal'), ('Biology', 'Ashish'), ('Chemistry', 'Eyad'), ('English', 'Jalal'), ('Health', 'Mushtag'), ('Islamic', 'Ahmed Alshar'), ('Math', 'ABDALLAH H'), ('Social', 'ASHRAF')]
}

def normalize_subject(subj):
    s = str(subj).lower()
    if 'math' in s or 'رياضيات' in s: return 'MATH'
    if 'english' in s or 'انجليزي' in s or 'إنجليزي' in s or 'لغة إنجليزية' in s: return 'ENGLISH'
    if 'science' in s or 'علوم' in s:
        if 'health' in s or 'صحية' in s: return 'HEALTH'
        return 'SCIENCE'
    if 'arabic' in s or 'عربي' in s or 'لغة عربية' in s: return 'ARABIC'
    if 'islamic' in s or 'إسلامية' in s or 'اسلامية' in s or 'تربية' in s: return 'ISLAMIC'
    if 'social' in s or 'اجتماعيات' in s or 'دراسات' in s: return 'SOCIAL'
    if 'physics' in s or 'فيزياء' in s: return 'PHYSICS'
    if 'chemistry' in s or 'كيمياء' in s: return 'CHEMISTRY'
    if 'biology' in s or 'احياء' in s or 'أحياء' in s: return 'BIOLOGY'
    if 'health' in s or 'صحية' in s: return 'HEALTH'
    if 'business' in s or 'إدارة' in s or 'b.a' in s: return 'BUSINESS'
    return 'UNKNOWN'

def normalize_class(cls_str):
    s = re.sub(r'[^A-Za-z0-9]', '', str(cls_str).upper())
    return s.replace('S1', '').replace('S2', '')

# Flatten master schedule
MASTER_SCHEDULE = []
for cls_name, subj_list in RAW_MASTER.items():
    for subj_name, teacher in subj_list:
        MASTER_SCHEDULE.append({
            'class_display': cls_name,
            'class_code': normalize_class(cls_name),
            'subject_display': subj_name,
            'subject_code': normalize_subject(subj_name),
            'teacher': teacher
        })

# ----------------- PDF GENERATOR LOGIC -----------------
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
    * {{ box-sizing: border-box; }}
    @page {{ size: A4 landscape; margin: 10mm; }}
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; color: #333; }}
    .header {{ text-align: center; color: #003366; border-bottom: 3px solid #003366; padding-bottom: 10px; margin-bottom: 15px; }}
    .header h2 {{ margin: 5px 0; font-size: 22px; }}
    .header h3 {{ margin: 5px 0; font-size: 16px; font-weight: normal; color: #555; }}
    .header h4 {{ margin: 10px 0 0 0; font-size: 18px; font-weight: bold; background-color: #003366; color: white; display: inline-block; padding: 8px 15px; border-radius: 5px; }}
    table {{ width: 100%; table-layout: fixed; border-collapse: collapse; margin-top: 10px; font-size: 11px; }}
    th, td {{ border: 1px solid #ddd; padding: 8px 5px; vertical-align: top; }}
    th {{ background-color: #003366; color: white; font-weight: bold; text-align: center; }}
    tr:nth-child(even) {{ background-color: #f9f9f9; }}
    .center-text {{ text-align: center; direction: ltr; }}
    .cell-content {{ word-wrap: break-word; overflow-wrap: break-word; word-break: break-word; white-space: pre-wrap; }}
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
            <th style="width: 10%;">الاثنين<br>Monday</th>
            <th style="width: 10%;">الثلاثاء<br>Tuesday</th>
            <th style="width: 10%;">الأربعاء<br>Wednesday</th>
            <th style="width: 10%;">الخميس<br>Thursday</th>
            <th style="width: 10%;">الجمعة<br>Friday</th>
            <th style="width: 25%;">نواتج التعلم<br>Learning Objectives</th>
        </tr>
        {rows}
    </table>
</body>
</html>"""

def clean_text(text):
    if pd.isna(text): return '-'
    t = str(text).strip()
    if not t: return '-'
    t = re.sub(r'(\S{35})', r'\1 ', t) 
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
    
    if file and file.filename.endswith('.xlsx'):
        file_id = str(uuid.uuid4())
        file_path = os.path.join('uploads', f"{file_id}.xlsx")
        file.save(file_path)
        
        try:
            df = pd.read_excel(file_path).fillna('')
            
            # Identify columns
            col_class = [c for c in df.columns if 'الصف' in c or 'Class' in c][0]
            col_subject = [c for c in df.columns if 'المادة' in c or 'Subject' in c][0]

            # Collect all submitted (Class, Subject) combinations
            submitted_combos = set()
            for _, row in df.iterrows():
                subj_code = normalize_subject(row[col_subject])
                classes = re.split(r'[;,]', str(row[col_class]))
                for c in classes:
                    c_clean = c.strip()
                    if c_clean:
                        submitted_combos.add((normalize_class(c_clean), subj_code))

            # Find missing entries
            missing_report = []
            for master in MASTER_SCHEDULE:
                if (master['class_code'], master['subject_code']) not in submitted_combos:
                    missing_report.append(master)
            
            # Pass data to the audit page
            return render_template('missing.html', missing=missing_report, file_id=file_id)

        except Exception as e:
            return f"An error occurred: {str(e)}", 500
            
    return "Invalid file format. Please upload an .xlsx file.", 400

@app.route('/generate/<file_id>', methods=['POST'])
def generate_zip(file_id):
    file_path = os.path.join('uploads', f"{file_id}.xlsx")
    if not os.path.exists(file_path):
        return "File not found or session expired", 400
        
    try:
        df = pd.read_excel(file_path).fillna('')
        
        col_class = [c for c in df.columns if 'الصف' in c or 'Class' in c][0]
        col_subject = [c for c in df.columns if 'المادة' in c or 'Subject' in c][0]
        col_teacher = [c for c in df.columns if 'Teacher' in c or 'اسم المعلم' in c][0]
        col_mon = [c for c in df.columns if 'Monday' in c or 'الاثنين' in c][0]
        col_tue = [c for c in df.columns if 'Tuesday' in c or 'الثلاثاء' in c][0]
        col_wed = [c for c in df.columns if 'Wednesday' in c or 'الأربعاء' in c][0]
        col_thu = [c for c in df.columns if 'Thursday' in c or 'الخميس' in c][0]
        col_fri = [c for c in df.columns if 'Friday' in c or 'الجمعة' in c][0]
        col_outcomes = [c for c in df.columns if 'Learning' in c or 'نواتج' in c][0]

        all_classes = set()
        for val in df[col_class]:
            parts = re.split(r'[;,]', str(val))
            for p in parts:
                p_clean = p.strip()
                if p_clean:
                    all_classes.add(p_clean)
        all_classes = sorted(list(all_classes))

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
                    <td><div dir="auto" class="cell-content"><strong>{clean_text(row[col_subject])}</strong></div></td>
                    <td><div dir="auto" class="cell-content"><strong>{clean_text(row[col_teacher])}</strong></div></td>
                    <td class="center-text"><div dir="auto" class="cell-content">{cls}</div></td>
                    <td><div dir="auto" class="cell-content">{clean_text(row[col_mon])}</div></td>
                    <td><div dir="auto" class="cell-content">{clean_text(row[col_tue])}</div></td>
                    <td><div dir="auto" class="cell-content">{clean_text(row[col_wed])}</div></td>
                    <td><div dir="auto" class="cell-content">{clean_text(row[col_thu])}</div></td>
                    <td><div dir="auto" class="cell-content">{clean_text(row[col_fri])}</div></td>
                    <td><div dir="auto" class="cell-content">{clean_text(row[col_outcomes])}</div></td>
                </tr>"""
                    rows_html += r_html
                    
                final_html = HTML_TEMPLATE.format(class_name=cls, rows=rows_html)
                safe_name = re.sub(r'[\\/*?:\[\]]', '', cls).replace(' ', '_')
                pdf_path = os.path.join(temp_dir, f"{safe_name}.pdf")
                
                HTML(string=final_html).write_pdf(pdf_path)
                pdf_files.append(pdf_path)

            zip_path = os.path.join(temp_dir, "Weekly_Lesson_Plans.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for pf in pdf_files:
                    zipf.write(pf, os.path.basename(pf))
            
            return send_file(zip_path, as_attachment=True, download_name="Weekly_Lesson_Plans.zip")
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

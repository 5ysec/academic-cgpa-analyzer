import streamlit as st
import pandas as pd
import pdfplumber
import re

# Define the standard grading scale
GRADE_SCALE = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'E': 1, 'F': 0}

def extract_crf_data(crf_file):
    """Extract Course Codes, Units, and Semesters from the CRF PDF."""
    crf_data = []
    current_level = ""
    current_semester = ""
    
    with pdfplumber.open(crf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            # Look for Level indicators (e.g., "Level: 100")
            level_match = re.search(r"Level:\s*(\d{3})", text)
            if level_match:
                current_level = f"Level {level_match.group(1)}"
            
            # Split text by lines to track semester headers
            lines = text.split('\n')
            for line in lines:
                if "First Semester" in line:
                    current_semester = "1st"
                elif "Second Semester" in line:
                    current_semester = "2nd"
                
                # Regex to match course lines
                course_match = re.search(r"(\b[A-Z]{3}\d{4}\b).*?(\d)$", line)
                if course_match and current_level and current_semester:
                    course_code = course_match.group(1)
                    units = float(course_match.group(2)) # Converted to float for Streamlit UI compatibility
                    semester_info = f"{current_level} - {current_semester}"
                    
                    crf_data.append({
                        "Course Code": course_code,
                        "Units": units,
                        "Semester": semester_info
                    })
                    
    return pd.DataFrame(crf_data)

def extract_apr_data(apr_file):
    """Extract Course Codes and Grades from the Academic Performance Result PDF."""
    apr_data = []
    
    with pdfplumber.open(apr_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            pattern = r"([A-Z]{3}\d{4})(?:(?![A-Z]{3}\d{4}).)+?\b([A-F])\b\s*\d{4}/\d{4}"
            matches = re.finditer(pattern, text)
            
            for match in matches:
                apr_data.append({
                    "Course Code": match.group(1),
                    "Grade": match.group(2)
                })
                    
    # Drop duplicates in case a course appears multiple times
    return pd.DataFrame(apr_data).drop_duplicates(subset=["Course Code"], keep='last')

def calculate_metrics(df):
    """Calculates total units, points, CGPA, and individual Semester GPAs."""
    total_points = 0
    total_units = 0
    breakdown_log = []
    semester_breakdown = {}
    
    if 'Semester' not in df.columns:
        df['Semester'] = 'Uncategorized'

    for semester_name, group in df.groupby('Semester'):
        sem_units = 0
        sem_points = 0
        
        for _, row in group.iterrows():
            course = str(row['Course Code']).strip()
            grade = str(row['Grade']).upper().strip()
            units = pd.to_numeric(row['Units'], errors='coerce')
            
            if pd.notna(units) and grade in GRADE_SCALE:
                grade_value = GRADE_SCALE[grade]
                points = units * grade_value
                
                sem_points += points
                sem_units += units
                total_points += points
                total_units += units
                
                breakdown_log.append(
                    f"**{course} ({semester_name})**: {units:g} Units × {grade_value} Points = **{points:g} Points**"
                )
        
        if sem_units > 0:
            semester_breakdown[semester_name] = round(sem_points / sem_units, 2)

    cgpa = total_points / total_units if total_units > 0 else 0.0
    return total_units, total_points, round(cgpa, 2), breakdown_log, semester_breakdown

def main():
    st.set_page_config(page_title="Automated CGPA Calculator", layout="centered")
    st.title("🎓 Automated CGPA Calculator")
    
    # --- Session State Initialization ---
    # We use session state so the extracted data survives app reruns
    if "course_data" not in st.session_state:
        st.session_state.course_data = pd.DataFrame([
            {"Semester": "", "Course Code": "", "Units": 0.0, "Grade": ""}
        ])

    with st.expander("📚 Academic Terminology & Grading Scale Guide"):
        st.markdown("""
        ### Key Terms
        * **CU (Credit Unit):** The academic weight or value assigned to a specific course.
        * **GP (Grade Point):** The points earned for a single course (CU × Grade Value).
        * **GPA:** Your average score for a single semester.
        * **CGPA:** Your overall academic average.
        
        ### The 5-Point Grading Scale
        * **A:** 5 points | **B:** 4 points | **C:** 3 points | **D:** 2 points | **E:** 1 point | **F:** 0 points
        """)

    # --- UI Layout using Tabs ---
    tab1, tab2 = st.tabs(["📄 Auto-Extract from PDFs", "📝 Manual / CSV Entry"])

    with tab1:
        st.markdown("Upload your official **Course Registration Form (CRF)** PDFs and your **Academic Performance Result (APR)** PDF to automatically populate your grades.")
        col_pdf1, col_pdf2 = st.columns(2)
        
        with col_pdf1:
            # NEW: Allow multiple files for CRFs
            crf_files = st.file_uploader("1. Upload CRF PDFs (Multiple allowed)", type=["pdf"], accept_multiple_files=True)
        with col_pdf2:
            apr_file = st.file_uploader("2. Upload APR PDF", type=["pdf"])
            
        if st.button("Extract & Merge Data", type="primary"):
            if crf_files and apr_file:
                with st.spinner("Parsing PDFs and merging data..."):
                    
                    # --- NEW: Loop through all uploaded CRFs and combine them ---
                    crf_dfs = []
                    for file in crf_files:
                        df = extract_crf_data(file)
                        if not df.empty:
                            crf_dfs.append(df)
                    
                    # If we successfully extracted data from the CRFs, combine them into one DataFrame
                    if crf_dfs:
                        crf_df = pd.concat(crf_dfs, ignore_index=True)
                        # Drop duplicates just in case a carry-over course appears on two different CRFs
                        crf_df = crf_df.drop_duplicates(subset=["Course Code"], keep='last')
                    else:
                        crf_df = pd.DataFrame() # Fallback if empty

                    # Extract the APR data
                    apr_df = extract_apr_data(apr_file)
                    
                    if not crf_df.empty and not apr_df.empty:
                        # Merge the combined CRF master list with the APR grades
                        merged_df = pd.merge(crf_df, apr_df, on="Course Code", how="left")
                        merged_df['Grade'] = merged_df['Grade'].fillna('Pending')
                        
                        # Reorder columns for the UI
                        merged_df = merged_df[['Semester', 'Course Code', 'Units', 'Grade']]
                        
                        # Update session state and refresh
                        st.session_state.course_data = merged_df
                        st.success(f"Successfully extracted {len(crf_files)} CRF(s) and merged with APR!")
                    else:
                        st.error("Could not extract valid data. Please ensure the PDFs are readable.")
            else:
                st.warning("Please upload at least one CRF and your APR PDF to extract data.")

    with tab2:
        uploaded_csv = st.file_uploader("Upload an existing CSV file", type=["csv"])
        if uploaded_csv:
            try:
                st.session_state.course_data = pd.read_csv(uploaded_csv)
                st.success("CSV loaded successfully!")
            except Exception as e:
                st.error(f"Error reading CSV: {e}")

    # --- Section 2: Interactive Data Entry ---
    st.subheader("Course Data Grid")
    st.caption("Review extracted data below. You can edit entries manually before calculating.")
    
    edited_df = st.data_editor(
        st.session_state.course_data,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Semester": st.column_config.TextColumn("Semester", required=True),
            "Course Code": st.column_config.TextColumn("Course Code", required=True),
            "Units": st.column_config.NumberColumn("Credit Units", min_value=1.0, max_value=6.0, step=1.0, required=True),
            "Grade": st.column_config.SelectboxColumn("Letter Grade", options=["A", "B", "C", "D", "E", "F", "Pending"], required=True)
        }
    )

    # Allow user to download the current grid state as CSV
    st.download_button(
        label="Download Current Grid as CSV",
        data=edited_df.to_csv(index=False).encode('utf-8'),
        file_name='My_Extracted_Grades.csv',
        mime='text/csv'
    )

    # --- Section 3: Calculation & Results ---
    st.divider()
    
    if st.button("Calculate Final CGPA", type="primary", use_container_width=True):
        # Filter out rows that are marked as 'Pending' or don't have valid grades
        valid_df = edited_df[edited_df['Grade'].isin(GRADE_SCALE.keys())]
        
        total_units, total_points, cgpa, breakdown_log, sem_breakdown = calculate_metrics(valid_df)
        
        st.markdown("### Cumulative Standing")
        col1, col2, col3 = st.columns(3)
        col1.metric(label="Total Credit Units", value=f"{total_units:g}")
        col2.metric(label="Total Grade Points", value=f"{total_points:g}")
        
        if cgpa >= 4.50:
            col3.metric(label="Final CGPA", value=f"{cgpa:.2f}", delta="First Class")
        elif cgpa >= 3.50:
            col3.metric(label="Final CGPA", value=f"{cgpa:.2f}", delta="Second Class Upper")
        else:
            col3.metric(label="Final CGPA", value=f"{cgpa:.2f}")

        st.markdown("### Semester Breakdown")
        sem_cols = st.columns(len(sem_breakdown) if len(sem_breakdown) > 0 else 1)
        
        for index, (sem_name, gpa) in enumerate(sem_breakdown.items()):
            with sem_cols[index % len(sem_cols)]:
                st.metric(label=str(sem_name), value=f"{gpa:.2f}")

        # --- NEW: Performance Trend Graph ---
        # Only show the graph if there is more than one semester to compare
        if len(sem_breakdown) > 1:
            st.markdown("### 📊 Performance Trend")
            
            # Convert the dictionary to a DataFrame and set the Semester as the index (X-axis)
            trend_df = pd.DataFrame(list(sem_breakdown.items()), columns=['Semester', 'GPA'])
            trend_df = trend_df.set_index('Semester')
            
            # Render a native Streamlit bar chart
            st.bar_chart(trend_df, y="GPA")

        if breakdown_log:
            with st.expander("🔍 See How This Was Calculated"):
                st.info("Formula: **Total Grade Points ÷ Total Credit Units**")
                
                st.markdown("### Step 1: Individual Course Points")
                for log in breakdown_log:
                    st.markdown(f"- {log}")
                    
                st.markdown("### Step 2: Final Division")
                st.markdown(f"{total_points:g} Points ÷ {total_units:g} Units = **{cgpa:.2f} CGPA**")
                
if __name__ == "__main__":
    main()
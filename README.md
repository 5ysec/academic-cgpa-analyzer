# 🎓 Automated Academic CGPA Calculator & Analytics Dashboard

An automated, web-based tool built with **Streamlit** to parse, merge, and analyze academic transcripts and registration forms. This application completely eliminates manual data entry by extracting modules, credit units, and grades directly from institutional PDF files, offering students an instant calculation of their individual semester GPAs, final CGPAs, and visual performance trajectories.

## 🚀 Key Features

* **Multi-File PDF Extraction:** Leverages `pdfplumber` and optimized regular expressions to automatically read and parse course codes, units, and semester tracking info from multiple **Course Registration Forms (CRFs)** simultaneously.
* **Grade Merging:** Extracts recorded grades from official **Academic Performance Result (APR)** sheets and maps them to the correct course codes pulled from your CRFs.
* **Interactive Data Grid:** Displays the parsed academic data in an editable UI grid using Streamlit's native data editor, allowing users to manually tweak figures, adjust credit weights, or handle pending statuses seamlessly.
* **Analytics & Visualizations:** Computes overall cumulative metrics and dynamically charts a **Semester Performance Trend** using clean bar graph components to visualize academic progress over time.
* **Educational Terminology Guide:** Includes a built-in collapsible lexicon defining critical university grading metrics (**CU, GP, GPA, CGPA**) alongside the standardized 5-point grading scale breakdown.
* **Data Portability:** Allows students to download their compiled and reviewed course grids as a clean `.csv` spreadsheet for backup or future use.

## 🛠️ Tech Stack & Architecture

This utility is structured entirely in Python, striking a balance between quick, scriptable file parsers and an elegant UI framework:
* **UI Framework:** Streamlit (Native web presentation layer)
* **Data Processing:** Pandas (DataFrame manipulation, indexing, and grouping operations)
* **PDF Parsing Engine:** pdfplumber & Regular Expressions (`re`)

## 📦 Installation & Local Setup

To clone and run this application locally on your machine, follow these steps:

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/5ysec/academic-cgpa-analyzer
   cd academic-cgpa-analyzer
   ```
2. **Set Up a Virtual Environment (Optional but Recommended)**
   ```bash
   python -m venv venv
   
  * **On Windows:**
    ```bash
    venv\Scripts\activate
    ```
  * **On macOS/Linux:**
    ```bash
    source venv/bin/activate
    ```
3. **Install the Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the Application:**
   ```bash
   streamlit run app.py
   ```
## 📖 How to Use the App

1. **Auto-Extraction:** Open the `Auto-Extract from PDFs` tab, drag and drop all your collected CRF PDFs (you can select multiple levels at once), and upload your APR PDF. Click **Extract & Merge Data**.

2. **Review Data:** Click over to the `Manual / CSV Entry` or check the `Course Data Grid` section below. Confirm that the extracted course units, semesters, and letter grades line up correctly. You can double-click any cell to change it or press `+` to add a missing module.

3. **Process Analytics:** Hit the prominent **Calculate Final CGPA** button at the bottom. The app will immediately isolate valid graded courses, generate your cumulative metrics cards, compute separate semester-by-semester bars, and output an expandable step-by-step mathematical breakdown log.

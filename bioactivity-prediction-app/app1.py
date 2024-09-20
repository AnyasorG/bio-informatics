import streamlit as st
import pandas as pd
from PIL import Image
import subprocess
import os
import base64
import pickle

# Molecular descriptor calculator
def desc_calc():
    bashCommand = "java -Xms2G -Xmx2G -Djava.awt.headless=true -jar ./PaDEL-Descriptor/PaDEL-Descriptor.jar -removesalt -standardizenitro -fingerprints -descriptortypes ./PaDEL-Descriptor/PubchemFingerprinter.xml -dir ./ -file descriptors_output.csv"
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    
    if process.returncode == 0:
        os.remove('molecule.smi')
    else:
        st.error("Error calculating descriptors.")

# File download
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="prediction.csv">Download Predictions</a>'
    return href

# Model building
def build_model(input_data, load_data):
    load_model = pickle.load(open('acetylcholinesterase_model.pkl', 'rb'))
    prediction = load_model.predict(input_data)
    st.header('**Prediction output**')
    prediction_output = pd.Series(prediction, name='pIC50')
    molecule_name = pd.Series(load_data[1], name='molecule_name')
    df = pd.concat([molecule_name, prediction_output], axis=1)
    st.write(df)
    st.markdown(filedownload(df), unsafe_allow_html=True)

# Logo image
try:
    image = Image.open('logo.png')
    st.image(image, use_column_width=True)
except FileNotFoundError:
    st.warning("Logo image not found.")

# Page title
st.markdown("""
# Bioactivity Prediction App (Acetylcholinesterase)
""")

# Sidebar
with st.sidebar.header('1. Upload your CSV data'):
    uploaded_file = st.sidebar.file_uploader("Upload your input file", type=['txt'])
    st.sidebar.markdown("""
[Example input file](https://raw.githubusercontent.com/dataprofessor/bioactivity-prediction-app/main/example_acetylcholinesterase.txt)
""")

if st.sidebar.button('Predict'):
    if uploaded_file is not None:
        load_data = pd.read_table(uploaded_file, sep=' ', header=None)
        load_data.to_csv('molecule.smi', sep='\t', header=False, index=False)

        st.header('**Original input data**')
        st.write(load_data)

        with st.spinner("Calculating descriptors..."):
            desc_calc()

        # Read in calculated descriptors
        st.header('**Calculated molecular descriptors**')
        desc = pd.read_csv('descriptors_output.csv')
        st.write(desc)
        st.write(desc.shape)

        # Subset of descriptors from the model
        try:
            Xlist = list(pd.read_csv('descriptor_list.csv').columns)
            desc_subset = desc[Xlist]
            st.write(desc_subset)
            st.write(desc_subset.shape)

            build_model(desc_subset, load_data)
        except FileNotFoundError:
            st.error("Descriptor list file not found.")
    else:
        st.warning("Please upload a file to proceed with predictions.")
else:
    st.info('Upload input data in the sidebar to start!')

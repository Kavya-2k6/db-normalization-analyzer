# NormFlow – Database Normalization Engine

NormFlow is an interactive tool that performs step-by-step database normalization from 1NF to BCNF. It allows users to input relational schemas and functional dependencies, then visualizes the normalization process with clear decomposition outputs.

---

## 🚀 Features

- Attribute closure computation
- Candidate key detection
- Minimal cover generation
- 1NF, 2NF, 3NF, BCNF validation
- Step-by-step decomposition with lossless join
- Real-time visualization of schemas and dependencies

---

## 🧠 Concepts Implemented

- Functional Dependencies
- Attribute Closure
- Candidate Keys
- Minimal Cover
- Normal Forms (1NF → BCNF)
- Lossless Join Decomposition

---

## ⚙️ Tech Stack

- Python
- Streamlit

---

## 🖥️ How It Works

1. Input attributes and functional dependencies
2. Compute candidate keys and closures
3. Check violations for each normal form
4. View decomposed schemas at each stage (1NF → BCNF)

---

## ▶️ Run Locally

```bash
pip install streamlit
streamlit run assignment.py

---

## 📸 Preview

### Schema & Key Analysis
![Schema](assets/schema.png)

### Normalization Output (1NF → BCNF)
![Normalization](assets/normalization.png)

---

## 📌 Example Use Case

- Analyze a relation with given functional dependencies  
- Identify candidate keys  
- Automatically normalize step-by-step  
- Understand decomposition logic visually  

---

## 📚 Learning Value

This project demonstrates:
- Strong understanding of DB normalization algorithms  
- Algorithmic thinking (closure, keys, minimal cover)  
- Practical implementation of theoretical concepts  
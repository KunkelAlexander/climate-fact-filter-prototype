# Climate Fact Filter - Empower NGOs to separate fact from fiction

- *Authors*: Elise Van De Putte, Vicky Cornelis, Gilles Ghys, Verner Viisainen, Alexander Kunkel

- Empower NGOs to separate fact from fiction.

![Main screen of prototype](/screenshots/main.png?raw=true)
![Dashboard](/screenshots/dashboard.png?raw=true)

## Submission for ECF AI Hackathon Challenge 1: Combatting Misinformation and Fake News

### Topic
Vast amounts of misinformation on environmental issues are shared through mass media and amplified on social media. This project tackles the question:

**How can we leverage AI to identify and classify misinformation and fake news on climate in mass media, while working with journalists and editors to deliver credible, reliable, and compelling coverage?**

---

### Our Proposal
- **Input:** Social media post relevant to an NGO's topic.
- **Process:** Use an LLM (leveraging NGO publications) to fact-check the claim and produce a shareable social media post.

### Benefits
- Frees up NGO staff for core tasks.
- Extends the lifetime of reports.
- Generates easily shareable content.
- Enhances NGO brand/reputation.
- Counters misinformation effectively.

---

## Prototype Completed During Hackathon

### Technology
- **Frontend:** React
- **Backend:** Python (Flask)

### Features
- **Functional:**
  - Upload screenshots.
  - Query OpenAI API for fact-checking.
- **Planned but not yet functional:**
  - Integration with vectorized databases.
  - Social media sharing.
  - Gallery of verified posts.
  - Dashboard for analytics.

---

## Folder Structure

```plaintext
my-cross-platform-app
├── image_records.db
├── package-lock.json
├── package.json
├── pics
│   ├── flat_earth.jpg
│   ├── trump_2.png
│   ├── trump_3.jpg
│   ├── trump_4.jpg
│   └── warming.png
├── public
│   ├── favicon.ico
│   ├── index.html
│   ├── logo.jpg
│   ├── logo192.png
│   ├── logo512.png
│   ├── manifest.json
│   └── robots.txt
├── python
│   ├── logo.png
│   ├── rag.ipynb
│   ├── reports
│   │   └── 202407_TE_advanced_biofuels_report.pdf
│   ├── server.py
│   └── text.txt
├── README.md
├── screenshots
│   ├── dashboard.png
│   └── main.png
├── src
│   ├── App.css
│   ├── App.js
│   ├── App.test.js
│   ├── index.css
│   ├── index.js
│   ├── logo.svg
│   ├── reportWebVitals.js
│   ├── seal.png
│   └── setupTests.js
└── uploads
    ├── <hashed_input_images>
    ├── <hashed_output_images>
```

### Key Files and Their Purpose

#### **Frontend (React)**
- `App.js`: Core logic for the application, including image upload, analysis, and gallery display.
- `App.css`: Styling for the frontend.
- `index.js`: Main entry point for the React app.
- `App.test.js`: Test cases for frontend components.

#### **Backend (Python)**
- `server.py`: Flask backend handling image processing, fact-checking, and API endpoints.
- `rag.ipynb`: Jupyter Notebook for retrieval-augmented generation (RAG) model experiments.
- `text.txt`: Reference text for fact-checking experiments.
- `logo.png`: Branding logo used in the app.

#### **Reports**
- `202407_TE_advanced_biofuels_report.pdf`: Example report used for generating embeddings.

#### **Uploads**
- Contains processed and raw images for testing and gallery purposes.

#### **Database**
- `image_records.db`: SQLite database storing image hashes, file paths, extracted text, and fact-checking results.

---

## How to Run the Project

### Prerequisites
- Python 3.8+
- Node.js
- pip (Python package manager)

### Backend Setup
1. Navigate to the `python` folder.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the server:
   ```bash
   python server.py
   ```

### Frontend Setup
1. Navigate to the project root.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the frontend:
   ```bash
   npm start
   ```

---

## Future Improvements
- **Enhanced Fact-Checking:** Use fine-tuned models for climate-specific misinformation.
- **Database Integration:** Enable fast and scalable fact retrieval.
- **Social Media Sharing:** Streamline posting verified content directly to social platforms.
- **Analytics Dashboard:** Provide actionable insights into misinformation trends.

---

## Contributing
We welcome contributions! Please open an issue or submit a pull request.

---

## License
This project is licensed under the MIT License. See `LICENSE` for details.


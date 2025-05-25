# EnergyWise - Electricity Bill Analyzer

EnergyWise is a web application that uses artificial intelligence to analyze electricity bills, helping customers better understand their consumption, identify possible errors, and receive personalized advice to save money.

## Key Features

- **Bill Analysis**: Upload your electricity bill in PDF or image format (JPG, PNG) and get a detailed analysis.
- **Bill Comparison**: Compare the current bill with a previous one to identify variations in consumption and costs.
- **Anomaly Detection**: Identify possible errors or anomalies in bills.
- **Personalized Advice**: Receive suggestions on how to save energy and reduce costs.
- **Virtual Assistant**: Chat with an AI assistant to get answers to your questions about the bill.
- **Responsive Interface**: Works on desktop and mobile devices.

## Technologies Used

- **Backend**: Flask (REST API), Python
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **AI/ML**: AWS Strands Agents with Claude 3.5 Sonnet on Amazon Bedrock
- **OCR**: Pytesseract for text extraction from images and PDFs
- **Alternative Interface**: Streamlit for an alternative version of the application

## System Requirements

- Python 3.8+
- Tesseract OCR
- Poppler (for PDF conversion)
- AWS CLI configured with access to Amazon Bedrock

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/bolletta-analyzer.git
   cd bolletta-analyzer
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Tesseract OCR:
   - **macOS**: `brew install tesseract tesseract-lang`
   - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng`
   - **Windows**: Download the installer from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

5. Install Poppler:
   - **macOS**: `brew install poppler`
   - **Ubuntu/Debian**: `sudo apt-get install poppler-utils`
   - **Windows**: Download from [poppler-windows](http://blog.alivate.com.au/poppler-windows/)

6. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file with your AWS credentials and other configurations.

## Usage

### Flask Version

1. Start the Flask application:
   ```bash
   python app.py
   ```

2. Open your browser and go to `http://localhost:8080`

### Streamlit Version

1. Start the Streamlit application:
   ```bash
   streamlit run streamlit_app.py
   ```

2. The browser will automatically open with the Streamlit application.

## Project Structure

```
bolletta-analyzer/
├── app/                    # Flask application
│   ├── __init__.py         # Flask app initialization
│   ├── routes.py           # API routes
│   ├── services/           # Business logic services
│   │   ├── bill_analyzer.py    # Bill analysis with direct Bedrock (backup)
│   │   ├── strands_agent.py    # Strands Agent implementation
│   │   └── document_processor.py  # Document processing and OCR
│   ├── static/             # Static files (CSS, JS, images)
│   └── templates/          # HTML templates
├── venv/                   # Python virtual environment
├── .env                    # Environment variables
├── app.py                  # Flask application entry point
├── streamlit_app.py        # Alternative Streamlit application
└── README.md               # Documentation
```

## AWS Configuration

The application uses AWS Strands Agents with Amazon Bedrock for bill analysis. Make sure you have:

1. An AWS account with access to Amazon Bedrock
2. Configured AWS credentials locally (`~/.aws/credentials`)
3. Set the correct region in the `.env` file (default: us-east-1)
4. Access to the Claude 3.5 Sonnet model on Amazon Bedrock

## License

This project is released under the MIT license.

## Contact

For questions or support, contact [anespo28@gmail.com].

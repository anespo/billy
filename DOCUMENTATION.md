# EnergyWise - Technical Documentation

## Overview

EnergyWise is a web application designed to analyze electricity bills using artificial intelligence. The application extracts text from uploaded bills (PDF or images), analyzes the content using Amazon Bedrock's Claude 3.5 Sonnet model, and provides users with insights about their energy consumption, costs, and potential savings.

## Architecture

The application is built with a modular architecture:

1. **Frontend**: HTML/CSS/JavaScript with Bootstrap 5 for responsive design
2. **Backend**: Python with Flask for API endpoints
3. **AI Processing**: Amazon Bedrock with Claude 3.5 Sonnet for natural language processing
4. **OCR**: Pytesseract for text extraction from images and PDFs
5. **Alternative Interface**: Streamlit for a more interactive user experience

## Components

### Document Processing

The document processing pipeline handles the extraction of text from uploaded bills:

1. **File Upload**: Users upload PDF or image files through the web interface
2. **Format Detection**: The system identifies the file format and routes it to the appropriate processor
3. **OCR Processing**: 
   - For images: Direct OCR processing with Pytesseract
   - For PDFs: Conversion to images using pdf2image, then OCR processing
4. **Language Detection**: The system attempts OCR with Spanish first, then English as fallback
5. **Text Extraction**: The extracted text is stored for analysis

### Bill Analysis

The bill analysis component uses AI to interpret the extracted text:

1. **Text Preprocessing**: The extracted text is cleaned and formatted
2. **AI Analysis**: The text is sent to Amazon Bedrock's Claude 3.5 Sonnet model with a specialized prompt
3. **Data Extraction**: The AI identifies key information such as billing period, total amount, consumption, etc.
4. **Anomaly Detection**: The system identifies potential anomalies or errors in the bill
5. **Recommendations**: Based on the extracted data, the system generates personalized saving tips

### Bill Comparison

The comparison feature allows users to compare current bills with previous ones:

1. **Data Normalization**: Both bills' data are normalized for comparison
2. **Difference Calculation**: The system calculates differences in consumption and costs
3. **Trend Analysis**: The system identifies trends and patterns
4. **Anomaly Highlighting**: Any significant deviations are highlighted
5. **Explanation Generation**: The AI provides possible explanations for the differences

### Virtual Assistant

The virtual assistant provides an interactive way for users to ask questions about their bills:

1. **Context Loading**: The assistant loads the bill analysis data as context
2. **Query Processing**: User queries are processed by the AI model
3. **Response Generation**: The assistant generates responses based on the bill data
4. **Conversation History**: The system maintains a conversation history for context

## API Endpoints

### Flask API

- `GET /`: Serves the main application page
- `POST /upload`: Handles bill uploads and returns analysis results
- `POST /compare`: Compares two bills and returns the comparison results

## Data Flow

1. User uploads a bill through the web interface
2. The file is saved to the server and processed by the document processor
3. The extracted text is sent to the bill analyzer
4. The analyzer returns structured data about the bill
5. The results are displayed to the user in the web interface
6. If a previous bill is available, the user can request a comparison
7. The comparison results are displayed alongside the individual bill analysis

## Security Considerations

- **File Validation**: Only allowed file types (PDF, JPG, PNG) are accepted
- **File Size Limits**: Maximum file size is enforced to prevent abuse
- **Secure File Naming**: Files are renamed with UUIDs to prevent path traversal attacks
- **AWS Credentials**: AWS credentials are stored securely in environment variables

## Error Handling

The application includes comprehensive error handling:

- **OCR Failures**: If OCR fails with one language, the system tries alternative languages
- **AI Processing Errors**: If the AI model returns errors, they are logged and reported to the user
- **File Processing Errors**: If file processing fails, appropriate error messages are displayed

## Performance Optimization

- **Image Preprocessing**: Images are converted to grayscale to improve OCR accuracy
- **PDF Optimization**: PDFs are processed page by page to manage memory usage
- **Response Caching**: Common responses can be cached to improve performance

## Deployment

The application can be deployed in several ways:

1. **Local Development**: Run with Flask's development server or Streamlit
2. **Production Deployment**: Deploy with Gunicorn/uWSGI behind Nginx
3. **Containerization**: Docker configuration is available for containerized deployment
4. **Cloud Deployment**: Can be deployed on AWS, Azure, or Google Cloud

## Configuration

The application is configured through environment variables in the `.env` file:

- `AWS_REGION`: AWS region for Bedrock services
- `BEDROCK_MODEL_ID`: ID of the Claude model to use
- `UPLOAD_FOLDER`: Directory for uploaded files
- `MAX_CONTENT_LENGTH`: Maximum allowed file size
- `TESSDATA_PREFIX`: Path to Tesseract data files

## Troubleshooting

Common issues and solutions:

1. **OCR Language Errors**: Ensure Tesseract language packs are installed
2. **AWS Authentication Errors**: Verify AWS credentials and permissions
3. **PDF Processing Errors**: Ensure Poppler is correctly installed
4. **Memory Issues**: For large PDFs, increase available memory or process fewer pages at once

## Future Enhancements

Planned future enhancements include:

1. **Multi-language Support**: Support for additional languages beyond Spanish and English
2. **Historical Data Analysis**: Track consumption and costs over time
3. **Energy Efficiency Recommendations**: More detailed recommendations based on usage patterns
4. **Mobile App**: Native mobile applications for iOS and Android
5. **Integration with Smart Meters**: Direct data import from smart meters

## License

This project is released under the MIT license.

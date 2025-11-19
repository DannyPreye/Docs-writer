"""
Enhanced PDF Reader Tool for CrewAI
Provides better text extraction using pdfplumber and includes table extraction capabilities.
"""

import io
import requests
from crewai.tools import BaseTool
from typing import Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
load_dotenv()

BRIGHT_DATA_API_KEY = os.getenv("BRIGHT_DATA_API_KEY")
BRIGHT_DATA_ZONE = os.getenv("BRIGHT_DATA_ZONE")

# Headers and data will be created dynamically in the tool methods



class EnhancedPDFReaderTool(BaseTool):
    name: str = "Enhanced PDF Reader"
    description: str = (
        "Reads and extracts text content from PDF files given a URL with better layout preservation. "
        "Can handle complex PDFs with tables and formatted text. "
        "Input should be a valid URL pointing to a PDF file."
    )

    def _run(self, pdf_url: str) -> str:
        """
        Download and extract text from a PDF URL using pdfplumber for better extraction.

        Args:
            pdf_url (str): The URL of the PDF file to read

        Returns:
            str: Extracted text content from the PDF
        """
        try:
            import pdfplumber
        except ImportError:
            return "Error: pdfplumber is not installed. Install it with: pip install pdfplumber"

        try:
            # Download the PDF
            response = requests.get(pdf_url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()

            # Check if the content is actually a PDF
            content_type = response.headers.get('content-type', '')
            if 'application/pdf' not in content_type.lower() and not pdf_url.lower().endswith('.pdf'):
                return f"Error: URL does not appear to point to a PDF file. Content-Type: {content_type}"

            # Read PDF from bytes
            pdf_file = io.BytesIO(response.content)

            # Extract text using pdfplumber
            extracted_text = ""
            with pdfplumber.open(pdf_file) as pdf:
                num_pages = len(pdf.pages)

                for page_num, page in enumerate(pdf.pages, 1):
                    extracted_text += f"\n{'='*60}\n"
                    extracted_text += f"Page {page_num}/{num_pages}\n"
                    extracted_text += f"{'='*60}\n\n"

                    # Extract text
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n"

                    # Extract tables if any
                    tables = page.extract_tables()
                    if tables:
                        extracted_text += f"\n[Found {len(tables)} table(s) on this page]\n"
                        for table_num, table in enumerate(tables, 1):
                            extracted_text += f"\nTable {table_num}:\n"
                            for row in table:
                                extracted_text += " | ".join([str(cell) if cell else "" for cell in row]) + "\n"
                            extracted_text += "\n"

            if not extracted_text.strip():
                return "Warning: PDF was read successfully but no text content was extracted. The PDF might be image-based or scanned."

            return extracted_text.strip()

        except requests.exceptions.Timeout:
            return f"Error: Request timed out while trying to download PDF from {pdf_url}"
        except requests.exceptions.RequestException as e:
            return f"Error downloading PDF: {str(e)}"
        except Exception as e:
            return f"Error processing PDF: {str(e)}"


class PDFMetadataReaderTool(BaseTool):

    name: str = "PDF Metadata Reader"
    description: str = (
        "Extracts metadata information from a PDF file given a URL. "
        "Returns information like title, author, subject, creation date, and number of pages. "
        "Input should be a valid URL pointing to a PDF file."
    )

    def _run(self, pdf_url: str) -> str:
        """
        Download and extract metadata from a PDF URL.

        Args:
            pdf_url (str): The URL of the PDF file

        Returns:
            str: Formatted metadata information
        """
        try:
            from pypdf import PdfReader

            # Download the PDF
            response = requests.get(pdf_url, timeout=30)
            response.raise_for_status()

            # Read PDF
            pdf_file = io.BytesIO(response.content)
            reader = PdfReader(pdf_file)

            # Extract metadata
            metadata = reader.metadata
            num_pages = len(reader.pages)

            result = f"PDF Metadata for: {pdf_url}\n"
            result += f"{'='*60}\n"
            result += f"Number of pages: {num_pages}\n"

            if metadata:
                if metadata.title:
                    result += f"Title: {metadata.title}\n"
                if metadata.author:
                    result += f"Author: {metadata.author}\n"
                if metadata.subject:
                    result += f"Subject: {metadata.subject}\n"
                if metadata.creator:
                    result += f"Creator: {metadata.creator}\n"
                if metadata.producer:
                    result += f"Producer: {metadata.producer}\n"
                if metadata.creation_date:
                    result += f"Creation Date: {metadata.creation_date}\n"
                if metadata.modification_date:
                    result += f"Modification Date: {metadata.modification_date}\n"
            else:
                result += "No metadata found in PDF.\n"

            return result

        except Exception as e:
            return f"Error reading PDF metadata: {str(e)}"

class BrightDataWebUnlockerTool(BaseTool):
    name: str = "BrightData Web Unlocker"
    description: str = (
        "Unlocks and scrapes clean content from a website using BrightData's Web Unlocker API. "
        "Input should be a valid URL of the website to unlock and scrape. "
        "Returns only clean, readable text content without HTML markup."
    )

    def _run(self, url: str) -> str:
        """
        Unlock and scrape clean content from a website using BrightData's Web Unlocker API.
        """
        print(f"🌐 Making BrightData API request to: {url}")
        try:
            # Prepare the request data for BrightData API (following official documentation)
            data = {
                "zone": BRIGHT_DATA_ZONE,
                "url": url,
                "format": "raw"  # Changed from "html" to "raw" as per documentation
            }

            headers = {
                "Authorization": f"Bearer {BRIGHT_DATA_API_KEY}",
                "Content-Type": "application/json"
            }

            # Make the API request to the correct BrightData endpoint
            api_url = "https://api.brightdata.com/request"  # Correct endpoint from documentation
            print(f"🌐 Making BrightData API request to: {api_url}")
            print(f"📋 Request data: {data}")

            response = requests.post(api_url, json=data, headers=headers)  # Correct parameter order

            # Check for errors and provide detailed information
            if response.status_code != 200:
                print(f"❌ BrightData API Error: {response.status_code}")
                print(f"Response: {response.text}")
                return f"BrightData API Error {response.status_code}: {response.text}"

            response.raise_for_status()

            # Since we're using "raw" format, the response should be HTML content
            # Parse HTML and extract clean content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside", "menu", "sidebar"]):
                element.decompose()

            # Extract text from main content areas
            content_selectors = [
                'main', 'article', '.content', '.main-content', '.post-content',
                '.entry-content', '.article-content', '.text-content', '.body-content',
                '[role="main"]', '.page-content', '.post-body', '.entry-body'
            ]

            text_content = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    for element in elements:
                        text_content += element.get_text(separator=' ', strip=True) + "\n"
                    break

            # If no main content found, get text from body
            if not text_content.strip():
                body = soup.find('body')
                if body:
                    text_content = body.get_text(separator=' ', strip=True)
                else:
                    text_content = soup.get_text(separator=' ', strip=True)

            # Clean up the text
            cleaned_content = self._clean_text(text_content)

            # Limit content length to prevent token overflow
            max_length = 15000
            if len(cleaned_content) > max_length:
                cleaned_content = self._truncate_intelligently(cleaned_content, max_length)

            return cleaned_content

        except Exception as e:
            print(f"❌ BrightData error: {str(e)}")
            print(f"🔄 Falling back to regular web scraping...")

            # Fallback to regular requests
            try:
                # requests and BeautifulSoup are already imported at the top

                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }

                response = requests.get(url, headers=headers, timeout=30)

                # Handle common HTTP errors gracefully
                if response.status_code == 403:
                    return f"Access denied (403 Forbidden) for {url}. This site may require special access or be protected against automated requests."
                elif response.status_code == 404:
                    return f"Page not found (404) for {url}."
                elif response.status_code != 200:
                    return f"HTTP {response.status_code} error for {url}."

                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                # Remove unwanted elements
                for element in soup(["script", "style", "nav", "footer", "header", "aside", "menu", "sidebar"]):
                    element.decompose()

                # Extract text content
                text_content = soup.get_text(separator=' ', strip=True)
                cleaned_content = self._clean_text(text_content)

                # Limit content length
                max_length = 15000
                if len(cleaned_content) > max_length:
                    cleaned_content = self._truncate_intelligently(cleaned_content, max_length)

                print(f"✅ Fallback scraping completed: {len(cleaned_content)} characters")
                return cleaned_content

            except Exception as fallback_error:
                return f"Error unlocking website: {str(e)} (Fallback also failed: {str(fallback_error)})"
        except requests.exceptions.RequestException as e:
            print(f"❌ BrightData request error: {str(e)}")
            return f"Error unlocking website: {str(e)}"

    def _clean_text(self, text: str) -> str:
        """Clean and format the extracted text"""
        # Split into lines and clean each line
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            # Skip empty lines, very short lines, and navigation elements
            if (len(line) > 15 and
                not line.isdigit() and
                not line.startswith(('http://', 'https://', 'www.')) and
                not line.lower().startswith(('click here', 'read more', 'learn more', 'view all'))):
                cleaned_lines.append(line)

        # Join lines and clean up multiple spaces
        result = '\n'.join(cleaned_lines)
        result = ' '.join(result.split())  # Remove multiple spaces

        return result

    def _truncate_intelligently(self, text: str, max_length: int) -> str:
        """Truncate text at a good breaking point"""
        if len(text) <= max_length:
            return text

        # Try to find a good truncation point
        truncated = text[:max_length]

        # Find the last complete sentence
        last_period = truncated.rfind('.')
        last_exclamation = truncated.rfind('!')
        last_question = truncated.rfind('?')
        last_newline = truncated.rfind('\n')

        # Use the best truncation point
        truncate_at = max(last_period, last_exclamation, last_question, last_newline)

        if truncate_at > max_length * 0.8:  # Only if we can keep 80% of content
            truncated = truncated[:truncate_at + 1]

        return truncated + f"\n\n[Content truncated from {len(text)} to {len(truncated)} characters]"

# Example usage with CrewAI
if __name__ == "__main__":
    from crewai import Agent, Task, Crew

    # Initialize the tools
    pdf_reader = EnhancedPDFReaderTool()
    pdf_metadata = PDFMetadataReaderTool()

    # Create an agent with the PDF reading capability
    research_agent = Agent(
        role='Research Analyst',
        goal='Extract and analyze information from PDF documents',
        backstory='An expert at reading and analyzing PDF documents to extract key insights.',
        tools=[pdf_reader, pdf_metadata],
        verbose=True
    )

    # Create a task
    analysis_task = Task(
        description="""
        Read the PDF document from the provided URL and extract all important information.
        Provide a summary of the key points found in the document.

        PDF URL: https://www.example.com/document.pdf
        """,
        agent=research_agent,
        expected_output="A comprehensive summary of the PDF content with key insights."
    )

    # Create and run the crew
    crew = Crew(
        agents=[research_agent],
        tasks=[analysis_task],
        verbose=True
    )

    # Execute
    result = crew.kickoff()
    print(result)

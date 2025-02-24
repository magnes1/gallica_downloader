import requests
from urllib.parse import quote
import xml.etree.ElementTree as ET

# Base URL for the OCR API
OCR_BASEURL = "https://gallica.bnf.fr/RequestDigitalElement?O="

# Step 1: Search for a document using the SRU endpoint
def search_gallica(search_term):
    """Search for documents containing the search term."""
    # URL-encode the search term
    encoded_query = quote(f'(gallica all "{search_term}")')
    search_url = f"https://gallica.bnf.fr/SRU?operation=searchRetrieve&version=1.2&query={encoded_query}&startRecord=1"
    
    # Send the request
    response = requests.get(search_url)
    if response.status_code == 200:
        return response.text  # Return the raw XML response
    else:
        raise Exception(f"Error: Unable to fetch search results (HTTP {response.status_code})")

# Step 2: Parse the XML response to extract ARKs and metadata
def parse_search_results(xml_response):
    """Parse the XML response to extract ARKs and metadata."""
    # Print the raw XML for debugging
    print("Raw XML Response:")
    print(xml_response)

    # Parse the XML string into an ElementTree object
    root = ET.fromstring(xml_response)

    # Define the namespaces used in the XML
    namespaces = {
        "srw": "http://www.loc.gov/zing/srw/",  # Namespace for <searchRetrieveResponse>
        "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",  # Namespace for <oai_dc:dc>
        "dc": "http://purl.org/dc/elements/1.1/"  # Namespace for <dc:identifier>
    }

    # Initialize an empty list to store results
    results = []

    # Find all <srw:record> elements in the XML
    for record in root.findall(".//srw:record", namespaces):
        # Find the <oai_dc:dc> element inside the current <srw:record>
        oai_dc = record.find(".//oai_dc:dc", namespaces)
        
        if oai_dc is not None:
            # Extract metadata
            metadata = {
                "ark": oai_dc.find(".//dc:identifier", namespaces).text.split("ark:/12148/")[1],
                "publication_name": oai_dc.find(".//dc:source", namespaces).text if oai_dc.find(".//dc:source", namespaces) is not None else "Unknown",
                "author": oai_dc.find(".//dc:creator", namespaces).text if oai_dc.find(".//dc:creator", namespaces) is not None else "Unknown",
                "date": oai_dc.find(".//dc:date", namespaces).text if oai_dc.find(".//dc:date", namespaces) is not None else "Unknown",
                "title": oai_dc.find(".//dc:title", namespaces).text if oai_dc.find(".//dc:title", namespaces) is not None else "Unknown"
            }
            results.append(metadata)

    # Return the list of results
    return results

# Step 3: Retrieve the OCR text of a document using its ARK identifier
def get_ocr_text(ark, page):
    """Retrieve the OCR text of a document using its ARK identifier."""
    # Construct the OCR API URL
    ocr_url = f"{OCR_BASEURL}{ark}&E=ALTO&Deb={page}"
    print(f"Fetching OCR text for page {page} from: {ocr_url}")

    # Send the request
    response = requests.get(ocr_url)
    if response.status_code == 200:
        return response.text  # Return the raw ALTO XML response
    else:
        raise Exception(f"Error: Unable to fetch OCR text for ARK {ark} (HTTP {response.status_code})")

# Step 4: Parse the ALTO XML to extract text
def parse_alto_xml(alto_xml):
    """Parse the ALTO XML to extract text."""
    # Parse the XML string into an ElementTree object
    root = ET.fromstring(alto_xml)

    # Define the ALTO namespace
    namespaces = {
        "alto": "http://www.loc.gov/standards/alto/ns-v3#"
    }

    # Extract text from all <String> elements
    text_lines = []
    for string in root.findall(".//alto:String", namespaces):
        text = string.get("CONTENT")
        if text:
            text_lines.append(text)

    # Join the text lines into a single string
    return "\n".join(text_lines)

# Step 5: Find sentences containing the search term in OCR text
def find_sentences_with_term(ark, search_term, max_pages=10):
    """Find sentences in a document that contain the search term."""
    sentences_with_term = []

    # Iterate through the first `max_pages` pages
    for page in range(1, max_pages + 1):
        try:
            # Fetch the OCR text for the current page
            alto_xml = get_ocr_text(ark, page)
            if alto_xml:
                # Parse the ALTO XML to extract text
                text = parse_alto_xml(alto_xml)
                # Split the text into sentences
                sentences = text.split(".")
                # Check if the search term is in any sentence
                for sentence in sentences:
                    if search_term.lower() in sentence.lower():
                        sentences_with_term.append(sentence.strip())
        except Exception as e:
            print(f"Error processing page {page}: {e}")

    return sentences_with_term

# Step 6: Main function to test the workflow
def main():
    search_term = "Panafricain"  # Replace with your search term
    try:
        search_results = search_gallica(search_term)
        if search_results:
            # Parse the XML to extract ARKs and metadata
            documents = parse_search_results(search_results)
            if documents:
                print(f"Found {len(documents)} documents in search results.")
                document = documents[0]  # Use the first document for testing
                print(f"Testing workflow for document: {document['title']} (ARK: {document['ark']})")

                # Find sentences containing the search term
                sentences = find_sentences_with_term(document["ark"], search_term, max_pages=10)
                if sentences:
                    print(f"The search term '{search_term}' was found in the following sentences:")
                    for sentence in sentences:
                        print(f"- {sentence}")
                else:
                    print(f"The search term '{search_term}' was not found in the first 10 pages.")
            else:
                print("No documents found in search results.")
        else:
            print("No search results found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
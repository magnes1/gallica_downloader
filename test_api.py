import requests
from urllib.parse import quote

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

# Step 2: Retrieve the text of a document using its ARK identifier
def get_document_text(ark):
    """Retrieve the full text of a document using its ARK identifier."""
    manifest_url = f"https://gallica.bnf.fr/iiif/ark:/12148/{ark}/manifest.json"
    response = requests.get(manifest_url)
    if response.status_code != 200:
        raise Exception(f"Error: Unable to fetch IIIF manifest for ARK {ark} (HTTP {response.status_code})")

    manifest = response.json()
    text_url = None

    # Find the text service URL in the manifest
    for sequence in manifest.get("sequences", []):
        for canvas in sequence.get("canvases", []):
            for resource in canvas.get("otherContent", []):
                if resource.get("@type") == "sc:AnnotationList":
                    text_url = resource.get("@id")
                    break
            if text_url:
                break
        if text_url:
            break

    if not text_url:
        raise Exception(f"No text content found for ARK {ark}")

    # Fetch the text content
    response = requests.get(text_url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error: Unable to fetch text content for ARK {ark} (HTTP {response.status_code})")

# Step 3: Main function to test text retrieval
def main():
    search_term = "Napoléon"  # Replace with your search term
    try:
        search_results = search_gallica(search_term)
        if search_results:
            print("Search results (raw XML):")
            print(search_results)  # Print the raw XML response

            # Parse the XML to extract ARKs (this is a placeholder; you'll need an XML parser)
            # For now, let's assume we have an ARK to test text retrieval
            ark = "bpt6k1234567"  # Replace with a valid ARK from the search results
            print(f"Testing text retrieval for ARK: {ark}")

            # Retrieve the text of the document
            text_data = get_document_text(ark)
            if text_data:
                print("Here's a sample of the text content:")
                for annotation in text_data.get("resources", [])[:5]:  # Print first 5 annotations
                    text = annotation.get("resource", {}).get("chars")
                    if text:
                        print(text)
            else:
                print("No text content found.")
        else:
            print("No search results found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
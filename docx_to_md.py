import base64
from lxml import etree

import docx
from docx.shared import Inches
from PIL import Image
import pytesseract
import io
import os
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
import openai
from openai import OpenAI

prompt = """
The following will be OCR extraction results of a screenshot of a Nursing master university test. 
The extraction will probably be in a difficult and hard to read format.
Your job will be to make sense of the content extracted by both extractors and try to rebuild it in a more readable, standardized format, using Markdown.

# REQUIREMENTS:
- The tests will be in Catalan, you are required to read them and provide the answers in Catalan.
- If extractions are not clear, still you must provide an answer. However, flag the question as unclear by adding a comment at the end of the answer: `No estic segur de la resposta correcta.`
- FOLLOW the provided output format for all questions.

# EXPECTED OUTPUT FORMAT (for each question):
---------------------
## PREGUNTA <numquestion>
### <question>
* a) <option_a>
* b) <option_b>
* c) <option_c>
* d) <option_d>

### RESPOSTA: (`<option>`)
```
<answer>
```
--------------------
Below you will find the information required from both extractors. Try to make sense of it and rebuild the content in a more readable format.

#CONTENT TO REBUILD:
## EXTRACTOR 1
{content1}

## EXTRACTOR 2
{content2}
"""

client = OpenAI(api_key="key")
LLM = ChatOpenAI(model="gpt-4o", api_key="key", temperature=0.5)


def extract_images_from_docx(docx_path):
    doc = docx.Document(docx_path)
    image_files = []

    # Define namespaces
    namespaces = {
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    }

    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            image_bytes = rel.target_part.blob
            image = Image.open(io.BytesIO(image_bytes))

            # Parse the XML to get cropping information
            docx_xml = doc.part.element.xml
            tree = etree.fromstring(docx_xml.encode('utf-8'))
            xpath = f'.//a:blip[@r:embed="{rel.rId}"]/../..'
            blip_element = tree.find(xpath, namespaces=namespaces)

            if blip_element is not None:
                crop_element = blip_element.find('.//a:srcRect', namespaces=namespaces)
                if crop_element is not None:
                    left_crop = int(crop_element.get('l', 0))
                    top_crop = int(crop_element.get('t', 0))
                    right_crop = int(crop_element.get('r', 0))
                    bottom_crop = int(crop_element.get('b', 0))

                    # Calculate cropping boundaries
                    left = image.width * left_crop // 100000
                    top = image.height * top_crop // 100000
                    right = image.width - (image.width * right_crop // 100000)
                    bottom = image.height - (image.height * bottom_crop // 100000)

                    # Crop the image
                    cropped_image = image.crop((left, top, right, bottom))
                else:
                    cropped_image = image
            else:
                cropped_image = image

            # Save cropped image to a byte array
            cropped_image_bytes = io.BytesIO()
            cropped_image.save(cropped_image_bytes, format=image.format)
            cropped_image_bytes = cropped_image_bytes.getvalue()

            image_files.append(cropped_image_bytes)

    return image_files


def save_images(image_files, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    image_paths = []

    for i, image_bytes in enumerate(image_files):
        image_path = os.path.join(output_dir, f'image_{i}.png')
        with open(image_path, 'wb') as f:
            f.write(image_bytes)
        image_paths.append(image_path)

    return image_paths

def image_to_text(image_path):
    # Function to encode the image
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    # Getting the base64 string
    base64_image = encode_image(image_path)

    # Using the OpenAI API to convert the image to text
    response = client.chat.completions.create(
            model="gpt-4o",
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "The following image is a screenshot of a nursery master test. The extraction will probably be missformatted and hard to read. Your job will be to make sense of the content and try to rebuild it in a more readable, standardized format, using Markdown."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
    )
    return response.choices[0].message.content

def extract_text_from_images(image_paths, output_dir, o_name):

    chain = (PromptTemplate(template=prompt, input_variables=["content"])
             | LLM
             | StrOutputParser())
    acc_text = []
    for i, image_path in enumerate(image_paths):
        text1 = ""
        try:
            text1 = image_to_text(image_path)
        except:
            pass

        image = Image.open(image_path)
        text2 = pytesseract.image_to_string(image)

        response = chain.invoke({"content1": text1, "content2": text2})
        print("--------response------------")
        print(response)

        acc_text.append(response)


        with open(f"{output_dir}/partial/texts/{o_name}-{i}.md", 'w') as f:
            f.write(response)

    with open(f"{output_dir}/{o_name}-COMPLET.md", "w") as f:
        f.write("\n\n".join(acc_text))


def main(docx_path):
    name = docx_path.split("/")[-1].replace(".docx", "").split(". ")[1]
    print(f"Processing {name}")
    dir_name = f"results/{name}"
    os.makedirs(f"{dir_name}/partial/texts", exist_ok=True)
    os.makedirs(f"{dir_name}/partial/images", exist_ok=True)
    image_files = extract_images_from_docx(docx_path)
    print(f"Extracted {len(image_files)} images")
    image_paths = save_images(image_files, f"{dir_name}/partial/images")
    extract_text_from_images(image_paths, dir_name, name)



if __name__ == "__main__":
    files = [f for f in os.listdir("data") if f.endswith(".docx")]
    files.sort()
    for file in files:
        veredict = input(f"> Proceed with `{file}`? (y/n): ".format(file))
        if veredict.lower() != "y":
            continue
        docx_path = f'data/{file}'  # Replace with the path to your DOCX file
        main(docx_path,)

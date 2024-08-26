import lxml.etree as ET
import tkinter as tk
from tkinter import messagebox, ttk
import pyperclip
from decimal import Decimal, ROUND_HALF_UP



def calculate_correct_values(xml_content):
    try:
        # Remove XML declaration if present
        if xml_content.startswith('<?xml'):
            xml_content = xml_content.split('?>', 1)[1]

        # Parse the XML content
        parser = ET.XMLParser(remove_blank_text=True)
        root = ET.fromstring(xml_content, parser)

        # Define namespaces
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

        # Initialize totals
        total_vProd = Decimal('0.00')
        total_vOutro = Decimal('0.00')

        # Iterate through each item
        for det in root.xpath('.//nfe:det', namespaces=ns):
            prod = det.find('nfe:prod', namespaces=ns)
            
            # Get product quantity and unit value
            qCom = Decimal(prod.find('nfe:qCom', namespaces=ns).text)
            vUnCom = Decimal(prod.find('nfe:vUnCom', namespaces=ns).text)
            
            # Calculate correct product value
            correct_vProd = (qCom * vUnCom).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Get current product value and other value
            current_vProd = Decimal(prod.find('nfe:vProd', namespaces=ns).text)
            vOutro = Decimal(prod.find('nfe:vOutro', namespaces=ns).text) if prod.find('nfe:vOutro', namespaces=ns) is not None else Decimal('0.00')
            
            # Calculate the difference
            difference = correct_vProd - current_vProd
            
            # Update the product value
            prod.find('nfe:vProd', namespaces=ns).text = str(correct_vProd)
            
            # Ensure the difference is added to vOutro
            if difference != 0:
                new_vOutro = (vOutro + abs(difference)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                if prod.find('nfe:vOutro', namespaces=ns) is not None:
                    prod.find('nfe:vOutro', namespaces=ns).text = str(new_vOutro)
                else:
                    # Create vOutro element before indTot
                    indTot = prod.find('nfe:indTot', namespaces=ns)
                    vOutro_elem = ET.Element('{http://www.portalfiscal.inf.br/nfe}vOutro')
                    vOutro_elem.text = str(new_vOutro)
                    prod.insert(prod.index(indTot), vOutro_elem)
                total_vOutro += abs(difference)
            
            # Update totals
            total_vProd += correct_vProd

        # Update the total section
        icmsTot = root.find('.//nfe:total/nfe:ICMSTot', namespaces=ns)
        current_total_vOutro = Decimal(icmsTot.find('nfe:vOutro', namespaces=ns).text) if icmsTot.find('nfe:vOutro', namespaces=ns) is not None else Decimal('0.00')
        icmsTot.find('nfe:vProd', namespaces=ns).text = str(total_vProd)
        icmsTot.find('nfe:vOutro', namespaces=ns).text = str((current_total_vOutro + total_vOutro).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

        # Remove namespaces for saving
        for elem in root.getiterator():
            if not hasattr(elem.tag, 'find'): continue
            i = elem.tag.find('}')
            if i > 0:
                elem.tag = elem.tag[i + 1:]

        # Convert modified XML back to string
        modified_xml = ET.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8').decode('utf-8')

        # Copy to clipboard
        pyperclip.copy(modified_xml)
        messagebox.showinfo("Sucesso", "XML foi corrigido e está na sua área de transferência!")

    except Exception as e:
        messagebox.showerror("Error", str(e))

def remove_dest_tag(xml_content):
    try:
        # Remove XML declaration if present and convert to bytes
        if xml_content.startswith('<?xml'):
            xml_content = xml_content.split('?>', 1)[1].strip()
        
        xml_content_bytes = xml_content.encode('utf-8')

        # Parse the XML content
        parser = ET.XMLParser(remove_blank_text=True)
        root = ET.fromstring(xml_content_bytes, parser)

        # Find and remove the <dest> element
        dest_elem = root.find('.//{http://www.portalfiscal.inf.br/nfe}dest')
        if dest_elem is not None:
            parent = dest_elem.getparent()
            parent.remove(dest_elem)

        # Convert modified XML back to string
        modified_xml = ET.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8').decode('utf-8')

        # Copy to clipboard
        pyperclip.copy(modified_xml)
        messagebox.showinfo("Sucesso", "Tag <dest> foi removida e o XML está na sua área de transferência!")

    except Exception as e:
        messagebox.showerror("Error", str(e))


# Setup Tkinter window
root = tk.Tk()
root.title("Ferramenta de XML")

notebook = ttk.Notebook(root)
notebook.pack(padx=10, pady=10, expand=True)

# Tab 1: Corrigir XML
frame1 = tk.Frame(notebook, padx=10, pady=10)
notebook.add(frame1, text="Corrigir vUnit")

label1 = tk.Label(frame1, text="Cole o Conteúdo do XML abaixo:")
label1.pack(pady=5)

text_area1 = tk.Text(frame1, height=20, width=80)
text_area1.pack(pady=5)

def process_text_correct_values():
    xml_content = text_area1.get("1.0", tk.END)
    calculate_correct_values(xml_content)

button1 = tk.Button(frame1, text="Corrigir o XML", command=process_text_correct_values)
button1.pack(pady=5)

# Tab 2: Remover Tag <dest>
frame2 = tk.Frame(notebook, padx=10, pady=10)
notebook.add(frame2, text="Remover Tag <dest>")

label2 = tk.Label(frame2, text="Cole o Conteúdo do XML abaixo:")
label2.pack(pady=5)

text_area2 = tk.Text(frame2, height=20, width=80)
text_area2.pack(pady=5)

def process_text_remove_dest():
    xml_content = text_area2.get("1.0", tk.END)
    remove_dest_tag(xml_content)

button2 = tk.Button(frame2, text="Remover Tag <dest>", command=process_text_remove_dest)
button2.pack(pady=5)

root.mainloop()

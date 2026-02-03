from fpdf import FPDF
# Nota: en fpdf 1.7.x output() retorna string en Python 3 (latin-1 encoded usually)
# Necesitamos manejarlo con cuidado para devolver bytes

class InformePDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'INFORME CLINICO PSICOLOGICO', 0, 1, 'C') # Sin acentos en header por compatibilidad basica
        self.set_font('Arial', '', 12)
        self.cell(0, 10, 'Mindset Psychology', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Pagina ' + str(self.page_no()), 0, 0, 'C')

def generate_pdf_report(paciente, psicologo, informe):
    pdf = InformePDF()
    pdf.add_page()
    
    # Colores y fuentes
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 11)
    
    # Cuadro Paciente
    pdf.cell(0, 8, ' DATOS DEL PACIENTE:', 0, 1, 'L', 1) # 1 = fill
    pdf.set_font('Arial', '', 11)
    
    # Helper para textos con posibles acentos
    def clean(text):
        if not text: return ""
        return text.encode('latin-1', 'replace').decode('latin-1')

    pdf.cell(0, 6, clean(f"Nombre: {paciente.nombre} {paciente.apellido}"), 0, 1)
    pdf.cell(0, 6, clean(f"DNI: {paciente.dni_nif if paciente.dni_nif else 'N/A'}"), 0, 1)
    pdf.cell(0, 6, f"Fecha Informe: {informe.fecha_creacion.strftime('%d/%m/%Y')}", 0, 1)
    pdf.ln(5)

    # Cuadro Profesional
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, ' DATOS DEL PROFESIONAL:', 0, 1, 'L', 1)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 6, clean(f"Psicologo/a: {psicologo.nombre} {psicologo.apellido}"), 0, 1)
    pdf.cell(0, 6, clean(f"N Colegiado: {psicologo.numero_colegiado if psicologo.numero_colegiado else 'N/A'}"), 0, 1)
    pdf.ln(10)

    # Secciones
    sections = [
        ("MOTIVO / TITULO", informe.titulo_informe),
        ("DIAGNOSTICO", informe.diagnostico),
        ("TRATAMIENTO", informe.tratamiento),
        ("OBSERVACIONES / CONTENIDO", informe.texto_informe)
    ]
    
    for title, content in sections:
        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 8, clean(title), 'B', 1, 'L')
        pdf.ln(2)
        
        pdf.set_font('Arial', '', 11)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 6, clean(content if content else "no consta."))
        pdf.ln(5)

    # Output FPDF 1.7.2
    # output(name, dest) -> dest='S' returns string
    try:
        pdf_content_string = pdf.output(dest='S')
        # En Python 3, fpdf devuelve string latin-1. Lo convertimos a bytes.
        return pdf_content_string.encode('latin-1')
    except Exception as e:
        print(f"Error generando PDF bytes: {e}")
        return None

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

    # Tareas / Ejercicios (Nueva seccion interactiva o de seguimiento)
    if hasattr(informe, 'tareas') and informe.tareas:
        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 8, clean("EJERCICIOS / TAREAS ASIGNADAS"), 'B', 1, 'L')
        pdf.ln(2)
        
        pdf.set_font('Arial', '', 11)
        pdf.set_text_color(0, 0, 0)
        for t in informe.tareas:
            status = "[X]" if t.completada else "[ ]"
            pdf.multi_cell(0, 6, clean(f" {status} {t.descripcion}"))
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
def generate_invoice_pdf(paciente, psicologo, factura):
    pdf = InformePDF() # Reutilizamos la clase base por simplicidad o creamos FacturaPDF
    pdf.add_page()
    
    # Colores y fuentes
    pdf.set_fill_color(30, 94, 255) # Azul primario de la app
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 14)
    
    # Helper para textos con posibles acentos
    def clean(text):
        if not text: return ""
        return str(text).encode('latin-1', 'replace').decode('latin-1')

    # Encabezado Factura
    pdf.cell(0, 15, clean(f" FACTURA: {factura.numero_factura}"), 0, 1, 'L', 1)
    pdf.ln(5)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 6, f"Fecha de Emision: {factura.fecha_emision.strftime('%d/%m/%Y')}", 0, 1)
    pdf.ln(5)

    # Datos emisor y receptor
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(95, 8, ' EMISOR (Psicologo/a):', 0, 0, 'L')
    pdf.cell(95, 8, ' RECEPTOR (Paciente):', 0, 1, 'L')
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(95, 6, clean(f"{psicologo.nombre} {psicologo.apellido}"), 0, 0)
    pdf.cell(95, 6, clean(f"{paciente.nombre} {paciente.apellido}"), 0, 1)
    
    pdf.cell(95, 6, clean(f"DNI/NIF: {psicologo.dni_nif if psicologo.dni_nif else 'N/A'}"), 0, 0)
    pdf.cell(95, 6, clean(f"DNI/NIF: {paciente.dni_nif if paciente.dni_nif else 'N/A'}"), 0, 1)
    
    pdf.cell(95, 6, clean(f"Direccion: {psicologo.direccion_fiscal if psicologo.direccion_fiscal else 'N/A'}"), 0, 0)
    pdf.cell(95, 6, clean(f"Direccion: {paciente.direccion_fiscal if paciente.direccion_fiscal else 'N/A'}"), 0, 1)
    
    pdf.ln(10)

    # Detalle Factura
    pdf.set_font('Arial', 'B', 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(140, 8, ' Concepto', 1, 0, 'L', 1)
    pdf.cell(50, 8, ' Importe', 1, 1, 'R', 1)
    
    pdf.set_font('Arial', '', 11)
    pdf.cell(140, 10, clean(factura.concepto if factura.concepto else "Sesion de Psicologia"), 1, 0, 'L')
    pdf.cell(50, 10, f"{factura.importe_total:.2f} EUR ", 1, 1, 'R')
    
    pdf.ln(10)
    
    # Totales
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(140, 8, 'Base Imponible:', 0, 0, 'R')
    pdf.cell(50, 8, f"{factura.base_imponible:.2f} EUR ", 0, 1, 'R')
    
    pdf.cell(140, 8, 'IVA (0%):', 0, 0, 'R') # Psicología suele estar exenta
    pdf.cell(50, 8, f"{factura.iva:.2f} EUR ", 0, 1, 'R')
    
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(30, 94, 255)
    pdf.cell(140, 12, 'TOTAL:', 0, 0, 'R')
    pdf.cell(50, 12, f"{factura.importe_total:.2f} EUR ", 0, 1, 'R')

    try:
        pdf_content_string = pdf.output(dest='S')
        return pdf_content_string.encode('latin-1')
    except Exception as e:
        print(f"Error generando PDF bytes de factura: {e}")
        return None

def generate_consent_pdf(paciente, psicologo, consentimiento):
    """Genera un PDF del consentimiento informado firmado."""
    pdf = FPDF()
    pdf.add_page()
    
    def clean(text):
        if not text: return ""
        return str(text).encode('latin-1', 'replace').decode('latin-1')

    # Header
    pdf.set_fill_color(30, 94, 255)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 15, ' CONSENTIMIENTO INFORMADO', 0, 1, 'L', 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, ' Proteccion de Datos - RGPD', 0, 1, 'L', 1)
    pdf.ln(10)

    # Datos
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 8, ' DATOS DEL PACIENTE', 0, 1, 'L', 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, clean(f"  Nombre: {paciente.nombre} {paciente.apellido}"), 0, 1)
    pdf.cell(0, 6, clean(f"  DNI/NIF: {paciente.dni_nif if paciente.dni_nif else 'N/A'}"), 0, 1)
    pdf.cell(0, 6, clean(f"  Email: {paciente.correo_electronico}"), 0, 1)
    pdf.ln(5)

    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, ' DATOS DEL PROFESIONAL', 0, 1, 'L', 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, clean(f"  Psicologo/a: {psicologo.nombre} {psicologo.apellido}"), 0, 1)
    pdf.cell(0, 6, clean(f"  N. Colegiado: {psicologo.numero_colegiado if psicologo.numero_colegiado else 'N/A'}"), 0, 1)
    pdf.ln(10)

    # Texto legal
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 8, 'CLAUSULAS DEL CONSENTIMIENTO', 'B', 1, 'L')
    pdf.ln(3)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(0, 0, 0)

    clausulas = [
        "1. FINALIDAD DEL TRATAMIENTO: Los datos personales y de salud proporcionados seran tratados exclusivamente con la finalidad de prestar servicios de atencion psicologica.",
        "2. BASE JURIDICA: El tratamiento se basa en el consentimiento explicito del paciente (Art. 6.1.a y Art. 9.2.a del RGPD) y en la necesidad de prestar asistencia sanitaria (Art. 9.2.h del RGPD).",
        "3. CONFIDENCIALIDAD: Toda la informacion compartida durante las sesiones es estrictamente confidencial, sujeta al secreto profesional regulado por el Codigo Deontologico del Psicologo.",
        "4. CONSERVACION: Los datos seran conservados durante el periodo necesario para cumplir con la finalidad para la que fueron recogidos y, como minimo, durante los plazos legales establecidos.",
        "5. DERECHOS: El paciente puede ejercer sus derechos de acceso, rectificacion, supresion, portabilidad, limitacion y oposicion contactando al profesional.",
        "6. REVOCACION: El paciente puede revocar este consentimiento en cualquier momento, sin que ello afecte a la licitud del tratamiento previo a la revocacion.",
        "7. MENORES: En caso de pacientes menores de edad, el consentimiento debera ser otorgado por sus representantes legales.",
        "8. COMUNICACION: Los datos no seran cedidos a terceros salvo obligacion legal o consentimiento expreso del paciente."
    ]

    for c in clausulas:
        pdf.multi_cell(0, 5, clean(c))
        pdf.ln(2)

    pdf.ln(5)

    # Firma
    pdf.set_font('Arial', 'B', 11)
    pdf.set_fill_color(230, 245, 230)
    pdf.cell(0, 8, ' ACEPTACION', 0, 1, 'L', 1)
    pdf.set_font('Arial', '', 10)
    fecha_str = consentimiento.fecha_aceptacion.strftime('%d/%m/%Y a las %H:%M:%S UTC')
    pdf.cell(0, 7, clean(f"  Aceptado digitalmente el {fecha_str}"), 0, 1)
    pdf.cell(0, 7, clean(f"  IP: {consentimiento.ip_address or 'N/A'}"), 0, 1)
    pdf.cell(0, 7, clean(f"  Version del documento: {consentimiento.version_documento}"), 0, 1)
    pdf.ln(5)

    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(128, 128, 128)
    pdf.multi_cell(0, 4, "Este documento ha sido generado automaticamente por la plataforma MindConnect y constituye prueba valida del consentimiento informado otorgado por el paciente de conformidad con el Reglamento General de Proteccion de Datos (UE) 2016/679.")

    try:
        pdf_content_string = pdf.output(dest='S')
        return pdf_content_string.encode('latin-1')
    except Exception as e:
        print(f"Error generando PDF de consentimiento: {e}")
        return None

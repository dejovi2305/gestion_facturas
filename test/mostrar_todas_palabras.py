import sys
from pathlib import Path

def mostrar_todas_palabras(ruta_pdf, ruta_salida="test/todas_palabras.png", numero_pagina=1):
    try:
        import pdfplumber
        from PIL import ImageDraw, ImageFont
    except ImportError as e:
        print(f"Error: Falta instalar dependencias")
        print(f"   {str(e)}")
        return
    
    try:
        with pdfplumber.open(ruta_pdf) as pdf:
            total_paginas = len(pdf.pages)
            
            if total_paginas == 0:
                print("El PDF no contiene paginas.")
                return
            
            if numero_pagina < 1 or numero_pagina > total_paginas:
                print(f"Numero de pagina invalido. El PDF tiene {total_paginas} pagina(s).")
                return
            
            pagina = pdf.pages[numero_pagina - 1]
            
            print("="*80)
            print("GENERANDO IMAGEN CON TODAS LAS PALABRAS DETECTADAS")
            print("="*80)
            print(f"\nTotal de paginas en el PDF: {total_paginas}")
            print(f"Procesando pagina: {numero_pagina}")
            print(f"Dimensiones: {pagina.width:.1f} x {pagina.height:.1f}")
            
            im = pagina.to_image(resolution=150)
            pil_img = im.original
            draw = ImageDraw.Draw(pil_img, "RGBA")
            
            palabras = pagina.extract_words()
            print(f"Total de palabras detectadas: {len(palabras)}\n")
            
            escala = 150 / 72
            
            try:
                font = ImageFont.truetype("arial.ttf", 8)
            except:
                font = ImageFont.load_default()
            
            print("Dibujando palabras...")
            for i, palabra in enumerate(palabras):
                x0 = palabra["x0"] * escala
                y0 = palabra["top"] * escala
                x1 = palabra["x1"] * escala
                y1 = palabra["bottom"] * escala
                
                if i % 4 == 0:
                    color = (255, 0, 0, 100)
                    outline = "red"
                elif i % 4 == 1:
                    color = (0, 255, 0, 100)
                    outline = "green"
                elif i % 4 == 2:
                    color = (0, 0, 255, 100)
                    outline = "blue"
                else:
                    color = (255, 165, 0, 100)
                    outline = "orange"
                
                draw.rectangle([x0, y0, x1, y1], fill=color, outline=outline, width=1)
                
                if i < 50:
                    draw.text((x0, y0 - 10), str(i+1), fill="black", font=font)
            
            print(f"\nGuardando imagen en: {ruta_salida}")
            pil_img.save(ruta_salida, "PNG")
            
            print("\n" + "="*80)
            print(f"Imagen generada exitosamente")
            print("="*80)
            
            print("\nPRIMERAS 400 PALABRAS DETECTADAS:")
            print("-" * 80)
            for i, palabra in enumerate(palabras[:400]):
                print(f"{i+1:3d}. '{palabra['text']:30s}' x0={palabra['x0']:6.1f} top={palabra['top']:6.1f} x1={palabra['x1']:6.1f} bottom={palabra['bottom']:6.1f}")
            
            if len(palabras) > 400:
                print(f"\n... y {len(palabras) - 400} palabras mas")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python test\\mostrar_todas_palabras.py <ruta_pdf> [numero_pagina]")
        print("\nEjemplos:")
        print("  python test\\mostrar_todas_palabras.py factura.pdf")
        print("  python test\\mostrar_todas_palabras.py factura.pdf 2")
        sys.exit(1)
    
    ruta_entrada = sys.argv[1]
    
    if len(sys.argv) == 2:
        numero_pag = 1
    else:
        numero_pag = int(sys.argv[2])
    
    ruta_salida = "test/todas_palabras.png"
    Path(ruta_salida).parent.mkdir(parents=True, exist_ok=True)
    
    mostrar_todas_palabras(ruta_entrada, ruta_salida, numero_pag)
